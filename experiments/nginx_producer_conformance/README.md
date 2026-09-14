# NGINX producer conformance

Separate finite producer experiment. No historical rescoring or production changes.

Run once into a fresh directory:

    python -B -m experiments.nginx_producer_conformance.run_experiment run

Read-only verification:

    python -B -m experiments.nginx_producer_conformance.run_experiment verify

The runner freezes protocol/implementation/configuration/resources and the baseline tracked inventory before HTTP requests. It uses the existing pinned target image. Raw request captures explicitly redact only temporary Basic-auth credentials; response and native-log bytes are unchanged. Manifest hashes establish custody, not authentication. No duplicate observed IDs is not a general uniqueness claim.
