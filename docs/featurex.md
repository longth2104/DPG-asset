# User

- Create google SSO ( the same as dpg e-learning)
- Instead of auto create a profile user whenever a new user log in, this app is only asscessible to manually added user.
- The process of adding user will be made by using the API from HRIS as follow:

    1. The admin will find user by calling the HRIS API and databse
    2. The added user will then be hierarchical organized. The users belong the parent company will have control ( view and edit ) to all asset, while the users belong to subsidiary company will only have control to asset belong to their company.

# Assset

- The information of the asset will be imported updated automatically from RDS including theirs id code , attached documents, logs, type, value, ...
- Each asset will also be attached with relevant document that can be exported and printed (according to the company guidline)
- The request feature also need to be accompanied with printable documents (templates will be updated later)


- Template : "C:\Users\BAN AI - 03\Downloads\Long"

- API: RDS and HRIS base URLs + API keys are now in `.env` (gitignored) —
  moved out of this file since it's tracked in git. See `RDS_*`/`HRIS_*` in
  `.env.example` for the variable names.