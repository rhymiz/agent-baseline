# Parcel lifecycle contract

This document defines the intended behavior.

## Ownership

`parcel.py` owns Parcel identity and the transition from queued to completed. The caller retains the original immutable value.

## Completion

`complete` accepts a queued Parcel and returns a new completed Parcel with the same identifier. A completed Parcel must be rejected with ValueError. Reprocessing is not supported.

## Verification

The repository uses only Python standard-library unittest. `make check` runs all tests under tests. No service, database, network, credentials, or package installation is needed.
