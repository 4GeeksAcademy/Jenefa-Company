# The Challenge
Your company's People & Talent department is in the middle of an active recruitment campaign. The open position received over 100 applications in less than two weeks, and the team is overwhelmed: they're tracking candidates in a shared spreadsheet, writing interview notes in separate documents, and updating statuses manually over email threads. The process is falling apart.

The Technology team has already built and exposed a REST API to manage the candidate pipeline. Your job is to build the frontend that the People team will use starting Monday. The system must let them see all candidates at a glance, filter them by status and stage, and access each candidate's full detail without losing context.

The Head of People has shared what they need with urgency:

What the tool must do
Show all candidates in a list — name, position, current status, and current stage at a glance.
Allow filtering by status and by stage, and searching by name or email without reloading the page.
Open a candidate's detail view and, from there, change their status or stage with a single interaction.
Add internal notes to a candidate and delete them when they're no longer relevant.
Register new candidates directly from the interface and edit a candidate's data when something needs to be corrected.
The API is ready and documented at https://playground.4geeks.com/tracker/api/v1/docs. All requests must be handled asynchronously — the UI must communicate loading states and handle errors gracefully. The team cannot afford a tool that breaks silently or leaves the user without feedback.

This is a real internal tool that real people will use from day one. Build it like one.