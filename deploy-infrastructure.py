import boto3
import json
import time

def deploy_beyonity_infrastructure():
    print("=" * 60)
    print("BEYONITY AWS INFRASTRUCTURE DEPLOYMENT")
    print("IT ADMINISTRATOR: Israr Sadaq")
    print("=" * 60)

    # AWS Clients
    s3 = boto3.client('s3')
    iam = boto3.client('iam')
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')

    account_id = "945504685795"
    bucket_name = f"beyonity-3d-assets-prod-{account_id}"
    backup_bucket = f"beyonity-backups-{account_id}"
    logs_bucket = f"beyonity-logs-{account_id}"
    client_share_bucket = f"beyonity-client-share-{account_id}"

    print(f"\n[1/5] CREATING S3 BUCKETS...")

    buckets = [
        bucket_name,
        backup_bucket,
        logs_bucket,
        client_share_bucket
    ]

    for bucket in buckets:
        try:
            s3.create_bucket(Bucket=bucket)
            print(f"  ✅ Created: {bucket}")
        except Exception as e:
            if "BucketAlreadyOwnedByYou" in str(e):
                print(f"  ⚠️ Already exists: {bucket}")
            else:
                print(f"  ❌ Error: {e}")

    # Enable Versioning on Production Bucket
    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={'Status': 'Enabled'}
    )
    print(f"  ✅ Versioning enabled on production bucket")

    # Enable Transfer Acceleration
    s3.put_bucket_accelerate_configuration(
        Bucket=bucket_name,
        AccelerateConfiguration={'Status': 'Enabled'}
    )
    print(f"  ✅ Transfer Acceleration enabled")

    print(f"\n[2/5] CREATING IAM GROUPS...")

    groups = [
        'Junior-Artists', 'Senior-Artists', 'Art-Directors',
        'IT-Admins', 'CTO-Executives', 'Finance', 'HR-Manager'
    ]

    for group in groups:
        try:
            iam.create_group(GroupName=group)
            print(f"  ✅ Created: {group}")
        except Exception as e:
            if "EntityAlreadyExists" in str(e):
                print(f"  ⚠️ Already exists: {group}")
            else:
                print(f"  ❌ Error: {e}")

    print(f"\n[3/5] CREATING IAM POLICIES...")

    # Junior Artist Policy
    junior_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/artists/*",
                f"arn:aws:s3:::{bucket_name}/shared/*"
            ]
        }]
    }

    # Senior Artist Policy
    senior_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/artists/*",
                    f"arn:aws:s3:::{bucket_name}/shared/*",
                    f"arn:aws:s3:::{bucket_name}/projects/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["ec2:DescribeInstances", "ec2:StartInstances", "ec2:StopInstances"],
                "Resource": "*"
            }
        ]
    }

    # Art Director Policy
    art_director_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:ListBucket", "s3:GetObject"],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/artists/*",
                    f"arn:aws:s3:::{bucket_name}/projects/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:DeleteObject"],
                "Resource": f"arn:aws:s3:::{bucket_name}/directors-cut/*"
            }
        ]
    }

    # IT Admin Policy
    admin_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:*", "iam:*", "ec2:*", "cloudwatch:*", "logs:*", "sns:*"],
            "Resource": "*"
        }]
    }

    policies = [
        ("Junior-Artist-Policy", junior_policy, ["Junior-Artists"]),
        ("Senior-Artist-Policy", senior_policy, ["Senior-Artists"]),
        ("Art-Director-Policy", art_director_policy, ["Art-Directors"]),
        ("IT-Admin-Policy", admin_policy, ["IT-Admins"])
    ]

    for policy_name, policy_doc, group_names in policies:
        try:
            response = iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_doc)
            )
            policy_arn = response['Policy']['Arn']
            print(f"  ✅ Created policy: {policy_name}")

            # Attach to groups
            for group in group_names:
                iam.attach_group_policy(GroupName=group, PolicyArn=policy_arn)
                print(f"     Attached to: {group}")
        except Exception as e:
            if "EntityAlreadyExists" in str(e):
                print(f"  ⚠️ Already exists: {policy_name}")
            else:
                print(f"  ❌ Error: {e}")

    print(f"\n[4/5] CREATING SNS TOPIC FOR ALERTS...")

    try:
        topic = sns.create_topic(Name='BeyonityS3Alerts')
        topic_arn = topic['TopicArn']
        print(f"  ✅ Created SNS Topic")

        sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint='israrsadaq057@gmail.com'
        )
        print(f"  ✅ Email subscription added for israrsadaq057@gmail.com")
    except Exception as e:
        print(f"  ⚠️ Topic may already exist: {e}")
        # Get existing topic ARN
        topics = sns.list_topics()
        for t in topics['Topics']:
            if 'BeyonityS3Alerts' in t['TopicArn']:
                topic_arn = t['TopicArn']
                break

    print(f"\n[5/5] CREATING CLOUDWATCH ALARMS...")

    alarms = [
        {
            'name': 'Beyonity-Production-Bucket-Size-Alarm',
            'metric': 'BucketSizeBytes',
            'threshold': 3298534883328,
            'period': 86400,
            'description': 'Alert when bucket exceeds 3 TB'
        },
        {
            'name': 'Beyonity-High-Request-Rate',
            'metric': 'AllRequests',
            'threshold': 1000,
            'period': 3600,
            'description': 'Alert when requests exceed 1000 per hour'
        },
        {
            'name': 'Beyonity-High-Error-Rate',
            'metric': '4xxErrors',
            'threshold': 10,
            'period': 3600,
            'description': 'Alert when errors exceed 10 per hour'
        }
    ]

    for alarm in alarms:
        try:
            cloudwatch.put_metric_alarm(
                AlarmName=alarm['name'],
                AlarmDescription=alarm['description'],
                MetricName=alarm['metric'],
                Namespace='AWS/S3',
                Statistic='Average' if alarm['metric'] == 'BucketSizeBytes' else 'Sum',
                Period=alarm['period'],
                EvaluationPeriods=1,
                Threshold=alarm['threshold'],
                ComparisonOperator='GreaterThanThreshold',
                Dimensions=[{'Name': 'BucketName', 'Value': bucket_name}],
                AlarmActions=[topic_arn]
            )
            print(f"  ✅ Created: {alarm['name']}")
        except Exception as e:
            print(f"  ⚠️ Could not create {alarm['name']}: {e}")

    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print(f"Production Bucket: {bucket_name}")
    print(f"SNS Topic: {topic_arn}")
    print("\n⚠️ Check your email to confirm SNS subscription!")
    print("=" * 60)

if __name__ == "__main__":
    deploy_beyonity_infrastructure()
