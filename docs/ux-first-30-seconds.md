# UX: First 30 Seconds Test

**Date:** 2026-09-07
**Purpose:** Verify a new user can understand Anexo_Risk within 30 seconds.

## Test Protocol

1. Open the application (no prior explanation)
2. Start timer
3. Ask user to observe the screen
4. After 30 seconds, ask:

### Questions

| # | Question | Expected Answer |
|---|---|---|
| 1 | What is this application for? | Emergency coordination / disaster response |
| 2 | What is the current situation? | Should reference map, alerts, or incidents |
| 3 | What looks most urgent? | Should reference severity colors or critical items |
| 4 | Who would use this? | Emergency operators, coordinators |

### Success Criteria

- User correctly identifies the app as emergency-related within 30 seconds
- User can point to at least one urgent item on the screen
- User understands the map shows geographic information

### What to Observe

- Where does the user's eyes go first?
- Do they notice the pilot warning banner?
- Do they understand the navigation tabs?
- Do they notice the status bar at the bottom?
- Do they understand the map markers?

### Common Failure Modes

- User thinks it's a weather app → UX needs improvement
- User can't find any incidents → Navigation unclear
- User doesn't understand severity colors → Legend insufficient
- User ignores the map → Layout issue

## Current UX Assessment

### What Works
- Map is immediately visible as the main content
- Severity colors (red/orange/yellow/green) are intuitive
- Navigation tabs are clearly labeled
- Pilot banner sets expectations

### Known Issues
- No onboarding tooltip for first-time users
- Map legend may be too small on mobile
- Command View toggle may be confusing without context
- Status bar at bottom may be overlooked

### Recommendations for Pilot
1. Keep the map as the default view (already done)
2. Ensure at least one incident is visible on first load
3. Consider a subtle "start here" indicator for first visit
4. The pilot banner helps set expectations

## Metrics to Collect

During actual pilot testing, measure:

| Metric | Target | How to Measure |
|---|---|---|
| Time to identify app purpose | < 15 seconds | Observation |
| Time to find an incident | < 30 seconds | Observation |
| Time to open Decision Center | < 60 seconds | Observation |
| Time to understand risk level | < 30 seconds | Post-test question |
| Task completion rate | > 80% | Structured test |
