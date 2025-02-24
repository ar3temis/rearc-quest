
## Part 1: AWS S3 & Sourcing Datasets
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

### S3 Links :
- [pr.class](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.class)
- [pr.contacts](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.contacts)
- [pr.data.0.Current](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.data.0.Current)
- [pr.data.1.AllData](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.data.1.AllData)
- [pr.duration](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.duration)
- [pr.footnote](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.footnote)
- [pr.measure](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.measure)
- [pr.period](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.period)
- [pr.seasonal](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.seasonal)
- [pr.series](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.series)
- [pr.sector](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.sector)
- [pr.txt](https://bls-gov-dataset.s3.ap-southeast-2.amazonaws.com/bls-data/pr.txt)



## Part 2: APIs
1. This part was straightforward until I saw the result of the JSON. Then figured
out we only want the “Data” key and “Source” key is redundant for this use
case
2. Again, defined a similar lambda function.



## Part 3: Data Analytics
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


## Part 4: Infrastructure as Code
1. This part was entirely new to me and took a lot of effort to understand. I hit the
limit on S3 free tier so could not test. But below are the extra steps that I took
which were not included when I was working on Part 1,2 and 3.

- **Creation of an EventBridge schedule to schedule the data fetching
lambdas daily**

<img width="1493" alt="image" src="https://github.com/user-attachments/assets/973239f6-8f72-4d53-9e68-dc92cc345ef4" />



- **Creation of S3 notifications which would get triggered whenever there
is an addition or deletion to the bucket**

<img width="1497" alt="image" src="https://github.com/user-attachments/assets/35548ed7-106e-465b-8833-ada3d3a8f212" />



- **Publishing of these notifications to an SQS Queue.**

- **Created one more lambda which would get triggered as soon as a
message arrived in the SQS Queue. This lambda was used to trigger
the Glue Job for performing data Analysis**


<img width="1493" alt="image" src="https://github.com/user-attachments/assets/3325476b-da6e-410c-b98e-291659d6cea0" />


3. This was done incrementally. Apologies for the undescriptive names. First
stack was for lambdas and buckets. Second stack included Queue. Allcomp was the final stack with all the components. Template code has been uploaded
<img width="1483" alt="image" src="https://github.com/user-attachments/assets/fbaf98a3-ae22-4ecd-b2bf-678f1bdeb7fa" />

4. Final Infrastructure as Code looked like below
<img width="1486" alt="image" src="https://github.com/user-attachments/assets/50b4fec7-63a0-4d0b-b783-da8c8ff8d5c5" />


