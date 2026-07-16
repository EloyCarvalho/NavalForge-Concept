# Traceability contract

Every principal result is wrapped with:

- calculation identifier;
- value and unit;
- method and equation;
- reference;
- active loading condition;
- geometry and weight revisions;
- algorithm version;
- relevant inputs;
- assumptions and warnings;
- compliance situation;
- execution timestamp.

The API returns this under `traceability`. Reports preserve the calculation
status, warnings and assumptions. Future rule plugins must retain the same
contract and add rule edition, clause and acceptance tolerance.
