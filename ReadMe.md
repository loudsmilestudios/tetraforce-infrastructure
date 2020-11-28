![Publish Release](https://github.com/josephbmanley/tetraforce-infrastructure/workflows/Publish%20Release/badge.svg) ![Build Stage](https://github.com/josephbmanley/tetraforce-infrastructure/workflows/Build%20Stage/badge.svg) 

# TetraForce Infrastructure

Backend services and infrastructure for managed [TetraForce](https://github.com/fornclake/TetraForce) servers.

![Infrastructure Diagram](https://static.cloudsumu.com/tetraforce/infrastructure.png)

## Community

- [Website](https://tetraforce.io/)
- [TetraForce Discord](https://discord.gg/cxTBVCZ)
- [TetraForce Patreon](https://www.patreon.com/tetraforce)

## Contributing

Feel free to look at [good first issues](https://github.com/josephbmanley/tetraforce-infrastructure/labels/good%20first%20issue), open an issue, or [join the community](#community) to start a conversation.

## Deploying

An important note, this stack will spin up AWS services that will cost money if used! By default this is a serverless stack running servers on Fargate, but be careful deploying your own environment!

### Deploying a dev environment

***Note:** At the moment, you must have contributor permissions to this repository to deploy a dev environment*

1. Go the [GitHub Actions](https://github.com/josephbmanley/tetraforce-infrastructure/actions) tab of this repository.

2. Navigate to the [Build Development Environment](https://github.com/josephbmanley/tetraforce-infrastructure/actions?query=workflow%3A%22Build+Development+Environment%22)

3. Click `Run Workflow` and select the branch you'd like to deploy from. (For most cases, this will be `master`)

    ![Infrastructure Diagram](https://static.cloudsumu.com/tetraforce/runworkflow.png)

4. Wait for your environment to be spun up!

To update your environment with the latest infrastucture, repeat the previous steps.

### Manual Deployment

#### Quick deploy

1. Create an AWS Account

2. Make sure you are logged in

3. Click the "Launch Stack" button

    [![Launch Stack](https://cdn.rawgit.com/buildkite/cloudformation-launch-stack-button-svg/master/launch-stack.svg)](https://console.aws.amazon.com/cloudformation/home#/stacks/create/template?stackName=TetraForce&templateURL=https://tetraforce-deployment-bucket-us-east-2.s3.amazonaws.com/production/cloudformation/tetraforce/top.yaml)

#### Deploy from Template

1. Download CloudFormation template:
    `https://tetraforce-deployment-bucket-us-east-2.s3.amazonaws.com/production/cloudformation/tetraforce/top.yaml`

    Download using wget: `wget https://tetraforce-deployment-bucket-us-east-2.s3.amazonaws.com/production/cloudformation/tetraforce/top.yaml -o tetraforce.yaml`

2. Deploy using your preferred deployment method:
    - [Using the AWS Command Line Interface](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-using-cli.html)
    - [Using the AWS CloudFormation console](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-using-console.html)