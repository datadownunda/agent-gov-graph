import json
from experiments.nginx_producer_conformance.run_experiment import PLAN, analyze


def evidence():
    captured=[]; native=[]
    for p in PLAN:
        rid=f'{p["request_number"]:032x}'
        captured.append({'response':f'HTTP/1.1 200 OK\r\nX-Request-ID: {rid}\r\nContent-Length: 1\r\n\r\nx'.encode()})
        native.append(dict(request_id=rid,incoming_x_request_id=p['sent_x_request_id'] or '',request_uri=p['uri'],request_method='GET',status=200,request_completion='OK',body_bytes_sent=1))
    return captured,native


def score(c,n,errors=None): return analyze(c,b''.join((json.dumps(x)+'\n').encode() for x in n),errors or [])


def test_supported_pairs_and_absence():
    c,n=evidence();rows,checks,decision=score(c,n)
    assert decision=='PRODUCER_CONTRACT_SUPPORTED'
    assert checks['pair_1_2_equal_incoming_distinct_native'] and checks['pair_7_8_equal_incoming_distinct_native']
    assert rows[2]['generated_equals_incoming'] is None
    assert all(r['matching_generated_id_requests']==[] for r in rows)


def test_duplicate_native_pair_is_contradicted():
    c,n=evidence();n[1]['request_id']=n[0]['request_id'];c[1]=c[0]
    rows,checks,decision=score(c,n)
    assert decision=='PRODUCER_CONTRACT_CONTRADICTED'
    assert rows[0]['matching_generated_id_requests']==[2]
    assert rows[1]['matching_generated_id_requests']==[1]


def test_real_substitution_is_conflation():
    c,n=evidence();n[0]['request_id']='SAME-VALUE';c[0]={'response':b'HTTP/1.1 200 OK\r\nX-Request-ID: SAME-VALUE\r\nContent-Length: 1\r\n\r\nx'}
    assert score(c,n)[2]=='FORWARDED_AND_GENERATED_IDS_CONFLATED'


def test_incomplete_capture_overrides_apparent_conflation():
    c,n=evidence();n[0]['request_id']='SAME-VALUE'
    assert score(c,n,['capture interrupted'])[2]=='NOT_EVALUABLE'
    assert score(c[:-1],n)[2]=='NOT_EVALUABLE'


def test_duplicate_response_header_is_not_evaluable():
    c,n=evidence();c[0]['response']=c[0]['response'].replace(b'Content-Length:',b'X-Request-ID: other\r\nContent-Length:')
    assert score(c,n)[2]=='NOT_EVALUABLE'


def test_wrong_uri_and_extra_native_row_are_not_evaluable():
    c,n=evidence();n[0]['request_uri']='/wrong'
    assert score(c,n)[2]=='NOT_EVALUABLE'
    c,n=evidence();assert score(c,n+[n[0]])[2]=='NOT_EVALUABLE'


def test_truncated_body_is_not_evaluable():
    c,n=evidence();c[0]['response']=c[0]['response'][:-1]
    assert score(c,n)[2]=='NOT_EVALUABLE'
