"""Replay preserved live M6 evidence and a separate deterministic positive fixture.

No new live target requests, model calls, enforcement or edits to M6 evidence.
Experiment names and evidence-kind labels are presentation metadata only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from uuid import UUID

from experiments.target_outcome.run_experiment import derive, TARGET
from src.authority_resolver import preserve_revision, resolve_authority, boundary_status
from src.control_attestation import attest, reconstruct_attestation
from src.evidence_digest import evidence_digest
from src.evidence_errors import InternalProcessingError
from src.governance_event import build_event

ROOT = Path(__file__).resolve().parents[2]
LIVE = ROOT / 'experiments/target_outcome/results/v1'


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    return {p.relative_to(directory).as_posix():digest(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and p != directory/'manifest.json'}


def create_positive_fixture(directory, control):
    """Build independently authored fixture records, not altered live M6 bytes.

    All timestamps, authority, governance and capture observations below are
    synthetic. No OPA or NGINX process runs to produce this positive fixture.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'native').mkdir()
    source = {'schema_version':'2.0','source_id':'deterministic-m7-authority-fixture','source_version':'1',
              'records':[{'authority_record_id':'fixture-authority','authority_version':'1',
                'principal':'fixture-agent','roles':['hr_investigator'],
                'permitted_scopes':[{'action':'read','resource_type':'employee_complaint','resource_ids':['complaint-456']}],
                'valid_from':'2026-09-05T00:00:00Z','valid_to':'2026-09-06T00:00:00Z'}]}
    revision = preserve_revision(source,directory/'authority_history')
    events = []
    for index, (name, allowed) in enumerate([('allow',True),('critical-deny',False),('blocked-deny',False)]):
        t = f'2026-09-05T12:00:{index:02d}Z'
        state = resolve_authority('fixture-agent',effective_at=t,registry_revision=source)
        binding = {'rule_version':'temporal-authority/1','authority_resolution_at':t,'opa_decision_at':t,
                   'revision':revision,'at_resolution':state,'at_opa_decision':state,
                   'status':boundary_status(state,state)}
        proposed = {'user':{'id':'fixture-agent','roles':['hr_investigator']},'action':'read',
                    'resource':{'id':'complaint-456' if allowed else 'complaint-789',
                                'type':'employee_complaint','classification':'restricted'}}
        decision = {'allowed':allowed,'decision':'ALLOW' if allowed else 'DENY',
                    'policy':'employee_complaint_access','policy_version':'1.0','reasons':[]}
        event = build_event(proposed,decision,context={'run_id':name,'step_id':'fixture',
                          'action_attempt_id':str(UUID(int=index+1)),'authority_binding':binding})
        event['event_id'] = str(UUID(int=index+10))
        event['timestamp'] = t
        events.append(event)
    (directory/'governance.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    (directory/'execution.jsonl').write_text('')
    (directory/'native/access.jsonl').write_text('')
    write(directory/'target.json',TARGET)
    write(directory/'identity_mapping.json',{'version':'1','entries':[]})
    shutil.copyfile(ROOT/'experiments/target_outcome/nginx.conf',directory/'nginx.conf')
    write(directory/'target_runtime.json',{'config_digest':digest(directory/'nginx.conf'),
          'producer':'DETERMINISTIC_FIXTURE_NO_TARGET_PROCESS'})
    write(directory/'blocked_coverage.json',{'schema_version':'1.0',
          'interval_start':'2026-09-05T12:00:02Z','interval_end':'2026-09-05T12:00:12Z',
          'roles':{'execution':'CAPTURED','outcome':'CAPTURED'},
          'scope':{'actor':{'namespace':'agent','id':'fixture-agent'},'action':'read',
                   'resource_id':'complaint-789','resource_type':'employee_complaint'},
          'basis':'Deterministic fixture observation interval; not a live empirical observation.'})
    _,correlations,views = derive(directory)  # Unchanged M6, not a new reconciliation rule.
    write(directory/'correlations.json',correlations)
    write(directory/'reconciliation.json',views)
    ref = views['blocked-bounded']['assertion_id']
    write(directory/'coverage_observations.json',{
        'schema_version':'1.0','control_digest':evidence_digest(control),'reconciliation_ref':ref,
        'target_id':TARGET['target_id'],'target_contract_digest':evidence_digest(TARGET),
        'scope':{'action':'read','resource_id':'complaint-789','resource_type':'employee_complaint'},
        'identity_scope':'ALL_TARGET_IDENTITIES',
        'capture':{'available':True,'finalized':True,'from':'2026-09-05T12:00:01Z',
                   'through':'2026-09-05T12:00:13Z','finalized_at':'2026-09-05T12:00:14Z',
                   'native_file_digest':digest(directory/'native/access.jsonl')},
        'clocks':{'maximum_offset_seconds':'0','basis':'Single deterministic fixture clock; not measured live synchronization.'},
        'unresolved_gaps':False,'candidate_ambiguity':False,
        'provenance':'SYNTHETIC_CONTROL_SPECIFIC_OBSERVATIONS; proves only the positive adjudication rule.'})
    write(directory/'manifest.json',{'schema_version':'1.0','files':inventory(directory),
          'provenance':'DETERMINISTIC_FIXTURE; no live NGINX or OPA observations.'})
    return ref


def run(directory):
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    control = json.loads((ROOT/'experiments/control_attestation/control.json').read_text())
    write(directory/'control.json',control)
    fixture = directory/'deterministic_fixture'
    positive_ref = create_positive_fixture(fixture,control)
    originals = json.loads((LIVE/'reconciliation.json').read_text())
    requests = [{'label':name,'evidence_kind':'PRESERVED_LIVE_M6',
                 'archive_reference':'repository:experiments/target_outcome/results/v1',
                 'assertion_ref':a['assertion_id'],'coverage_support':None} for name,a in originals.items()]
    requests.append({'label':'positive-rule-fixture','evidence_kind':'DETERMINISTIC_FIXTURE',
                     'archive_reference':'local:deterministic_fixture',
                     'assertion_ref':positive_ref,'coverage_support':'coverage_observations.json'})
    attestations, verifications = [], []
    for request in requests:
        archive = fixture if request['evidence_kind']=='DETERMINISTIC_FIXTURE' else LIVE
        attestation, receipt = attest(archive,request['assertion_ref'],control,coverage_support=request['coverage_support'])
        _require_completed(attestation, receipt)
        # Labels never enter attest() or adjudicate(). Metadata stays outside assertions.
        attestations.append({'evidence_kind':request['evidence_kind'],'label':request['label'],'attestation':attestation})
        verifications.append({'request':request,'receipt':receipt})
    write(directory/'attestations.json',attestations)
    write(directory/'verification.json',verifications)
    write(directory/'manifest.json',{'schema_version':'1.0','files':inventory(directory),
          'limitations':'Content inventory, not authenticated provenance. Fixture positivity is not live effectiveness.'})
    return audit_results(directory)


def _require_completed(attestation, receipt):
    if (
        attestation["evaluation_status"] == "INTERNAL_ERROR"
        or receipt["status"] == "INTERNAL_ERROR"
    ):
        raise InternalProcessingError(
            "M7 processing could not complete; replay agreement is undetermined"
        )


def audit_results(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["files"] != inventory(directory):
        raise ValueError("M7 results inventory or content changed")
    control = json.loads((directory / "control.json").read_text())
    assertions = json.loads((directory / "attestations.json").read_text())
    verifications = json.loads((directory / "verification.json").read_text())
    if len(assertions) != len(verifications):
        raise ValueError("Verification/attestation count mismatch")
    for wrapped, verification in zip(assertions, verifications):
        request = verification["request"]
        reference = request["archive_reference"]
        if reference == "repository:experiments/target_outcome/results/v1":
            archive = LIVE
            if request["evidence_kind"] != "PRESERVED_LIVE_M6":
                raise ValueError("Live evidence kind misrepresented")
        elif reference == "local:deterministic_fixture":
            archive = directory / "deterministic_fixture"
            if request["evidence_kind"] != "DETERMINISTIC_FIXTURE":
                raise ValueError("Fixture must not be represented as live evidence")
        else:
            raise ValueError("Unsupported archive reference")
        expected, receipt = attest(
            archive,
            request["assertion_ref"],
            control,
            coverage_support=request["coverage_support"],
        )
        _require_completed(expected, receipt)
        if (
            receipt != verification["receipt"]
            or expected != wrapped["attestation"]
            or wrapped["evidence_kind"] != request["evidence_kind"]
            or wrapped["label"] != request["label"]
        ):
            raise ValueError("M7 deterministic replay disagrees")
        reconstruction = reconstruct_attestation(
            expected, archive, control, coverage_support=request["coverage_support"]
        )
        if reconstruction["status"] == "INTERNAL_ERROR":
            raise InternalProcessingError("M7 reconstruction could not complete")
        if reconstruction["status"] != "VERIFIED":
            raise ValueError("M7 reconstruction failed")
    live = [
        a["attestation"]
        for a in assertions
        if a["evidence_kind"] == "PRESERVED_LIVE_M6"
    ]
    synthetic = [
        a["attestation"]
        for a in assertions
        if a["evidence_kind"] == "DETERMINISTIC_FIXTURE"
    ]
    return {
        "status": "VERIFIED",
        "attestations": len(assertions),
        "live_control_effective_demonstrated": any(
            a["finding"] == "CONTROL_EFFECTIVE" for a in live
        ),
        "deterministic_positive_rule_demonstrated": any(
            a["finding"] == "CONTROL_EFFECTIVE" for a in synthetic
        ),
        "live_findings": [
            {"evaluation_status": a["evaluation_status"], "finding": a["finding"]}
            for a in live
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['run','audit'])
    parser.add_argument('directory',type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory) if args.command=='run' else audit_results(args.directory),indent=2))


if __name__ == '__main__':
    main()
