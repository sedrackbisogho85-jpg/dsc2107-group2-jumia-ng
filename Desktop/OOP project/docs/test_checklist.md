# Test Checklist

Member 6 responsibility: reproducible evidence and integration results.

- [x] Run `python -m unittest test_app -v`
- [x] Run repository tests against an in-memory SQLite database
- [x] Verify successful and rejected dispensing
- [x] Verify branch-specific stock and transfer behaviour
- [ ] Perform the live Tkinter workflow in the desktop demonstration
- [ ] Record each team member's live oral-defence evidence

Before testing:

```text
python seed_data.py --reset
python -m unittest test_app -v
```
