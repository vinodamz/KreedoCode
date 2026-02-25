Kreedo Curriculum API Documentation
This document outlines the API endpoints used to fetch curriculum data, including grades, subjects, and activities for a school.

Workflow Overview

The process to get the full curriculum breakdown involves a sequence of three API calls:

Get Grades: Start by fetching all available grades for a specific school. This gives you the grade_id for each grade level.

Get Subjects: Use the grade_id from the first step to get all the subjects associated with that specific grade. This returns the subject_id and plan_id.

Get Activities: Use the subject_id and plan_id from the second step to retrieve the list of all activities for that subject.

1. Get Grades by School

This endpoint retrieves a list of all grades associated with a given school ID.

Method: GET

URL: https://6t.kreedo.solutions/api/plan/grades_by_school/{school_id}

Query Parameters:

school_id: (Required) The ID of the school. In the example, this is 2078.

type: (Required) The type of user making the request. Example: school_associate.

user_id: (Required) The ID of the user. Example: 169776.

Example Request:

https://6t.kreedo.solutions/api/plan/grades_by_school/2078?type=school_associate&user_id=169776

Key Response Fields:
The response is a JSON object containing a data array. Each object in the array represents a grade and contains a grade_id and grade_name.

grade_id: The unique identifier for the grade (e.g., 1, 2, 3, 4).

grade_name: The name of the grade (e.g., "Playgroup", "Nursery").

Sample Response Snippet:

{
    "statusCode": 200,
    "isSuccess": true,
    "message": "grades_by_school",
    "data": [
        {
            "id": 7347,
            "grade_label": "Playgroup",
            "grade_id": 1,
            "grade_name": "Playgroup",
            "school": 2078
        },
        {
            "id": 7346,
            "grade_label": "Nursery",
            "grade_id": 2,
            "grade_name": "Nursery",
            "school": 2078
        }
    ]
}

2. Get School Subject List

This endpoint retrieves the subjects for a specific grade.

Method: GET

URL: https://6t.kreedo.solutions/api/curriculum/school_subject_list

Query Parameters:

grade: (Required) The grade_id obtained from the first API call.

school: (Required) The ID of the school (e.g., 2078).

type: (Required) The type of user (e.g., school_associate).

user_id: (Required) The ID of the user (e.g., 169776).

is_kreedo: (Required) Set to true to get Kreedo subjects.

Example Request:

https://6t.kreedo.solutions/api/curriculum/school_subject_list?grade=1&school=2078&type=school_associate&user_id=169776&is_kreedo=true

Key Response Fields:
The response data is an array of subject objects.

id: The unique identifier for the subject. This is the subject_id needed for the next step.

subject_label: The display name of the subject (e.g., "Prewriting").

plan_id: The identifier for the subject's curriculum plan. This is needed for the next step.

subject.id: The underlying subject master ID.

Sample Response Snippet:

{
    "statusCode": 200,
    "isSuccess": true,
    "message": "school_subject_list",
    "data": [
        {
            "id": 87887,
            "subject_label": "Prewriting",
            "subject": {
                "id": 56,
                "name": "L0 - Prewriting"
            },
            "plan_id": 162
        },
        {
            "id": 87886,
            "subject_label": "Communication",
            "subject": {
                "id": 55,
                "name": "L0 - Communication"
            },
            "plan_id": 164
        }
    ]
}

3. Get Activity List by Tag

This endpoint retrieves all activities associated with a subject's plan.

Method: POST

URL: https://6t.kreedo.solutions/api/plan/get_activity_list_by_tag

Query Parameters:

block_no: (Optional) Can be left empty.

activity: (Optional) Can be left empty.

Request Body (JSON):

plan: (Required) The plan_id obtained from the "Get School Subject List" endpoint.

subject: (Required) The id (subject_id) obtained from the "Get School Subject List" endpoint.

act_tag_list: (Required) An array of activity tag IDs. Use [0] to fetch all activities.

Example Request Body:

{
    "plan": 162,
    "subject": 87887,
    "act_tag_list": [0]
}

Key Response Fields:
The response data is an array of activity objects.

activity: The unique identifier for the activity.

activity_name: The full name of the activity.

whatsapp_activity_name: A shortened name for the activity.

Sample Response Snippet:

{
    "isSuccess": true,
    "message": "Block Wise Plan Activity List",
    "statusCode": 200,
    "data": [
        {
            "activity": 14953,
            "activity_name": "LV_0 Prewriting Introduction Activity 1",
            "whatsapp_activity_name": "L0: Prewriting IA 1",
            "block_no": "",
            "block_name": ""
        },
        {
            "activity": 14954,
            "activity_name": "LV_0 Prewriting Introduction Activity 2",
            "whatsapp_activity_name": "L0: Prewriting IA 2",
            "block_no": "",
            "block_name": ""
        }
    ]
}

