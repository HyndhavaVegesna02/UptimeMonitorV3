# Console Deployment Runbook — Uptime Monitor V3

This runbook guides you through deploying the Uptime Monitor V3 application to AWS. It assumes no prior AWS CLI or CloudFormation command-line experience; the entire stack is created and managed directly via the AWS Console, with only ECR image push and frontend build performed locally.

---

## Prerequisites

Before beginning, ensure you have:
1. An AWS Account with administrator permissions.
2. The AWS CLI installed and configured locally (`aws configure`).
3. Docker installed and running locally.
4. Git branch `sprint-49` checked out.

---

## Step 1: CloudFormation Stack Creation

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/).
2. In the search bar at the top, type **CloudFormation** and select it.
3. Click the orange **Create stack** button and select **With new resources (standard)**.
4. Under **Prerequisite - Prepare template**, select **Template is ready**.
5. Under **Specify template**, select **Upload a template file**, click **Choose file**, and select the `infra/stack.yaml` file from the project root. Click **Next**.
6. Enter a **Stack name** (e.g., `uptime-monitor`).
7. In the **Parameters** section, fill in the following:
   - **ImageTag**: Keep as `latest`.
   - **APIDesiredCount**: Keep as `1`.
   - **LoopDesiredCount**: Keep as `1` (This is pinned to 1 to guarantee singleton loop execution and prevent double Statuspage publishes).
   - **CloudFrontPrefixListId**: You must look this up:
     - Open a new console tab, navigate to the **VPC** service.
     - Click **Managed Prefix Lists** on the left menu.
     - Search for `com.amazonaws.global.cloudfront.origin-facing`.
     - Copy the **Prefix list ID** (starts with `pl-...`, e.g., `pl-58a64931`) and paste it into the CloudFormation parameter.
8. Click **Next**, click **Next** again on the Configure stack options page.
9. Scroll to the bottom, check the checkbox **I acknowledge that AWS CloudFormation might create IAM resources**, and click **Submit**.
10. Wait for the stack status to transition to **CREATE_COMPLETE** (approx. 5-10 minutes).

---

## Step 2: Secrets Manager Value Configuration

1. In the AWS Console search bar, type **Secrets Manager** and select it.
2. You will see two secrets created by the stack:
   - `uptime-monitor-dynatrace-secrets`
   - `uptime-monitor-statuspage-secrets`
3. Configure the **Dynatrace secrets**:
   - Click on `uptime-monitor-dynatrace-secrets`.
   - Scroll down to the **Secret value** section and click **Retrieve secret value**.
   - Click **Edit**.
   - Select the **Key/value** tab and add the following keys and values:
     - `DYNATRACE_ENV_URL` = Your Dynatrace environment base URL (e.g., `https://xyz.live.dynatrace.com`)
     - `DYNATRACE_API_TOKEN` = Your Dynatrace Grail API platform token
   - Click **Save**.
4. Configure the **Statuspage secrets**:
   - Click on `uptime-monitor-statuspage-secrets`.
   - Scroll down and click **Retrieve secret value**, then **Edit**.
   - Select the **Key/value** tab and add the following keys and values:
     - `STATUSPAGE_PAGE_ID` = Your Statuspage page ID
     - `STATUSPAGE_API_KEY` = Your Statuspage API token
   - Click **Save**.

> **Do NOT start or restart the ECS services yet.** No image exists in ECR until Step 3,
> so tasks cannot launch. The services come up via the force-new-deployment at the end of
> Step 3, which starts tasks that read these secret values on boot.

### Environment variables injected by the stack (no console entry needed)

Besides the four secret-backed values above, the CloudFormation template injects these
**plain (non-secret) environment variables** into the task definitions — you do NOT enter
them anywhere; they are listed here so you know every variable each container receives:

| Variable | api service | loop service | Source |
| --- | :---: | :---: | --- |
| `AWS_REGION` | ✅ | ✅ | template (stack region) |
| `DYNAMO_OBSERVATIONS_TABLE` | ✅ | ✅ | template (observations table name) |
| `DYNAMO_CONTROL_TABLE` | ✅ | ✅ | template (control table name) |
| `DYNATRACE_ENV_URL` | — | ✅ | Secrets Manager (entered above) |
| `DYNATRACE_API_TOKEN` | — | ✅ | Secrets Manager (entered above) |
| `STATUSPAGE_PAGE_ID` | — | ✅ | Secrets Manager (entered above) |
| `STATUSPAGE_API_KEY` | — | ✅ | Secrets Manager (entered above) |

The api task runs the default image CMD (uvicorn); the loop task overrides the CMD to
`python -m src.composition.run` and is the only service that receives the Dynatrace/Statuspage
secrets.

---

## Step 3: Docker Build, Tag, and Push (ECR)

This is the only CLI step required.

1. Navigate to the **ECR** service in the AWS Console.
2. Click **Repositories** on the left and select `uptime-monitor-repo`.
3. In the top right corner, click the **View push commands** button.
4. Open your local terminal, navigate to the project root, and execute the push commands shown:
   - **Command 1 (Retrieve login token)**:
     ```bash
     aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<your-region>.amazonaws.com
     ```
   - **Command 2 (Build image)**:
     ```bash
     docker build -t uptime_monitor_v3:latest .
     ```
   - **Command 3 (Tag image)**:
     ```bash
     docker tag uptime_monitor_v3:latest <aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/uptime-monitor-repo:latest
     ```
   - **Command 4 (Push image)**:
     ```bash
     docker push <aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/uptime-monitor-repo:latest
     ```
5. Navigate to the **ECS** Console, go to **Clusters** -> `uptime-monitor-cluster` -> select the **Services** tab, select both services (`uptime-monitor-api` and `uptime-monitor-loop`), and click **Update** -> check **Force new deployment** -> click **Update** to pull the newly pushed image.

---

## Step 4: Frontend Build and Upload (S3)

1. In your local terminal, navigate to the `frontend/` directory and run:
   ```bash
   npm run build
   ```
   This will generate build output in `frontend/dist/`.
2. Go to the **S3** Console in AWS and find the bucket named `uptime-monitor-frontend-<account-id>`.
3. Click **Upload** and upload the entire contents of the `frontend/dist/` directory (ensure files like `index.html` and the `assets/` directory are uploaded directly to the root of the bucket).
4. After upload, clear the CloudFront cache:
   - Go to the **CloudFront** service in AWS Console.
   - Click on the distribution created by the stack.
   - Go to the **Invalidations** tab.
   - Click **Create invalidation**, type `/*` in the object path, and click **Invalidate**.

---

## Step 5: Verification Checklist

1. Go to the **CloudFormation** Console, click on your stack, and select the **Outputs** tab.
2. Click the link for the **CloudFrontDomainName**.
3. Verify the following:
   - [ ] All six dashboard tabs load and render successfully.
   - [ ] Clicking different tabs updates the routing and shows the UI.
   - [ ] The API requests (`/api/*`) load correctly without CORS or route errors.
   - [ ] Check the watermark timestamp on the Dashboard page to ensure the loop is running and advancing.
