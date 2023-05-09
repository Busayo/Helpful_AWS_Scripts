import boto3

# Create IAM client
iam = boto3.client('iam')

# Get all users
users = iam.list_users()['Users']

# Loop through users
for user in users:
    print(f"User: {user['UserName']}")

    # Get user's permissions
    policies = iam.list_attached_user_policies(
        UserName=user['UserName'])['AttachedPolicies']
    for policy in policies:
        print(f"\tAttached policy: {policy['PolicyName']}")

    groups = iam.list_groups_for_user(UserName=user['UserName'])['Groups']
    for group in groups:
        print(f"\tGroup: {group['GroupName']}")

        # Get group's policies
        policies = iam.list_attached_group_policies(
            GroupName=group['GroupName'])['AttachedPolicies']
        for policy in policies:
            print(f"\t\tAttached policy: {policy['PolicyName']}")

    print("")
