# System design (behaviour)

## Alert flow
1. Signals arrive: check-in answers, activity events (camera or wearable), fall events (confidence), SOS, missed care-plan reminders.
2. `evaluate()` builds the signals, `risk.assess()` scores them (rules; learned logistic model when enabled; **safety floor**: SOS is always Critical, an unanswered fall after the 60 s verification window is at least High). The reasons list explains the score.
3. A fall first **asks the person** ("Are you OK?") for `VERIFY_SECONDS`; "I'm OK" cancels it and the alert is recorded as resolved by the person (a false-alarm proxy).
4. If nobody answers the alert escalates by stage every `ESCALATION_STEP_SECONDS`: ask the person, notify the caregiver, escalate to the emergency contact. Notifications state the reasons. Acknowledging by a caregiver pauses escalation for `ACK_SNOOZE_MINUTES`.
5. Every risk change is logged (`risklog`) for trends and Power BI.

## Privacy
No images or videos are stored: pose estimation runs on the camera side, only 9 keypoints and an event leave it. Power BI exports contain no names or contacts. Caregivers only see their assigned people.

## Care plan
Reminders recorded by the caregiver (medication, meal, water, activity) with times and "done today"; missed ones feed the risk score. The system never diagnoses and never changes doses.

## Wearable path
A phone or wearable sends 3 s windows (150 x [x,y,z] in g at 50 Hz) to `/sensor/accel`; the scikit-learn pipeline returns a probability; at or above the model's validated threshold it becomes a `fall` event and follows steps 2-5. Refused (503) until a model trained on real data is installed.

## Roles
`admin` (everything, creates caregivers and people, demo data outside production), `caregiver` (assigned people), device key (cameras/wearables, can only post events), elder access code (own screen only).
