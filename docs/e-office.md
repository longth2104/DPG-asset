# Workflow

" Automize asset management"

- My employer want the asset related request-approved action to be performed on https://datphuong.vn/ .

- Once a reqest is approved, the action will be automatically triggered and saved in the log.

- In short, the ams will be a databse/log of for asset related action performed on https://datphuong.vn/

- Keep the existing function of the ams intact



1. Personal asset management

- On https://datphuong.vn/, each user is shown which asset they are in possession of. The process of asset assignment is performed on https://datphuong.vn/ with information taken from ams app.
- ams app have already has asset to HRIS for employess list.
- ams app have already has a list import function
- Now we need to create a feature that match the info on the list with the employee, especially their emails.
- Ams need to exposed its API so that when they actioned performed on https://datphuong.vn/, it has the information from ams and triggered the data changed in ams.

2. Request flow

- Any request - approved concerning asset (purchase, liquidification, ...) will be made in https://datphuong.vn/.
- Ams only need to exposed its API to provided https://datphuong.vn/ with the sufficient asset information , keep track with the changed made in https://datphuong.vn/, and save the action in the log