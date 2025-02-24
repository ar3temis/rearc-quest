# Working Notes/Thoughts/Documentation

Part 1: AWS S3 & Sourcing Datasets
1. Used Lambda for all data fetches as recommended in the quest itself
2. To fetch the first open dataset and keep it in sync, I explored aws s3 sync
which as per stackoverflow is battle tested and best for such scenarios.
However, I found out that Lambda has no native AWS CLI support. After more
research, figured that I’d have to either use a Lambda layer to package the
AWS CLI, or make a custom deployment package with CLI and my code.
3. Due to restrictions on the laptop, I was not able to download AWS CLI in local,
so that option went out of the window. Found a pre-package zip file on the
internet, but it seemed to miss other libraries that I required.
4. Finally, came across Content MD-5 which could be implemented by hashlib
python library and didn’t need any additional setup.
CODE:
S3 LINK (Create a static website for hosting)


Part 2: APIs
1. This part was straightforward until I saw the result of the JSON. Then figured
out we only want the “Data” key and “Source” key is redundant for this use
case
2. Again, defined a similar lambda function.
CODE:
S3 Link:


Part 3: Data Analytics
1. This was my favorite part, and it came at a cost. Which I will tell later
2. I explored many options to do this, AWS Sagemaker studio,creating own
notebook on EC2 (free-tier instance did not have enough memory) and AWS
Glue as well.
3. AWS Sagemaker is cheaper, but it doesn’t support spark natively. So, I tried to
use Pandas and ran into some array length issues with Json, the solution for
which was to trim down the lists. At that moment, it did not seem like a
possible approach.
4. Keeping in mind, that we want to trigger the analysis as soon as we get data
from API, I settled on AWS glue which not only offers Spark in its notebooks
and can also be scheduled as a job. Found out that Glue notebooks are
expensive as they have way more capabilities (incurred 10$)
CODE:
Notebook Link:

Part 4: Infrastructure as Code
1. This part was entirely new to me and took a lot of effort to understand. I hit the
limit on S3 free tier so could not test. But below are the extra steps that I took
which were not included when I was working on Part 1,2 and 3.
a. Creation of an EventBridge schedule to schedule the data fetching
lambdas daily
b. Creation of S3 notifications which would get triggered whenever there
is an addition or deletion to the bucket
c. Publishing of these notifications to an SQS Queue
d. Created one more lambda which would get triggered as soon as a
message arrived in the SQS Queue. This lambda was used to trigger
the Glue Job for performing data Analysis
2. This was done incrementally. Apologies for the undescriptive names. First
stack was for lambdas and buckets. Second stack included Queue.
<img width="1483" alt="image" src="https://github.com/user-attachments/assets/fbaf98a3-ae22-4ecd-b2bf-678f1bdeb7fa" />

3. Final Iac looked like below
<img width="1486" alt="image" src="https://github.com/user-attachments/assets/50b4fec7-63a0-4d0b-b783-da8c8ff8d5c5" />


