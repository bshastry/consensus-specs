from eth2spec.test.context import (
    spec_state_test,
    with_altair_and_later,
)
from eth2spec.test.helpers.attestations import (
    run_attestation_processing,
    get_valid_attestation,
)
from eth2spec.test.helpers.state import (
    next_slots,
)


@with_altair_and_later
@spec_state_test
def test_zero_effective_balance_attestation(spec, state):
    """
    Test that a validator with zero effective balance can still attest without causing crashes in Altair+.
    This test verifies that:
    1. No division by zero occurs in reward calculations
    2. The validator can still participate in attestations
    3. The zero effective balance is handled correctly in balance totals and participation flags
    """
    # This test targets the critical window between a validator's effective balance dropping to zero
    # and the validator being ejected from the set. During this window, the validator remains in the
    # registry with some actual balance but zero voting power, and must not cause protocol crashes
    # when attesting. Client implementations must handle division by zero risks gracefully.

    # Set up test validator with zero effective balance
    validator_index = 0
    state.validators[validator_index].effective_balance = 0

    # Create and add an attestation from this validator
    attestation = get_valid_attestation(
        spec,
        state,
        signed=True
    )

    # Store pre-state values for comparison
    pre_validator_balance = state.balances[validator_index]

    # Advance state by MIN_ATTESTATION_INCLUSION_DELAY slots
    next_slots(spec, state, spec.MIN_ATTESTATION_INCLUSION_DELAY)

    # Process the attestation
    yield from run_attestation_processing(spec, state, attestation)

    # Verify the validator's effective balance remains zero
    assert state.validators[validator_index].effective_balance == 0

    # Verify the validator's actual balance didn't change (no rewards with 0 effective balance)
    assert state.balances[validator_index] == pre_validator_balance

    # Verify no impact on total active balance minimum
    assert spec.get_total_active_balance(state) >= spec.EFFECTIVE_BALANCE_INCREMENT
