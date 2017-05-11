# Notice
This repo is based on https://github.com/awslabs/amazon-polly-sample but with big modifications:
1. This one does not include the ZIP file pachage but instead gives you the instructions on how to use Docker to build the package (see end of this README)
2. Updated requirements (upgraded AWSCLI)
3. Updated S3 URL format in the lamdba_function code (using Environment variables for the bucket's region)


# Amazon Polly Sample
This app allows you to easily convert any publicly available RSS content into audio Podcasts, so you can listen to your favorite blogs on mobile devices instead of reading them.

# Requirements
You will need an AWS account and an RSS feed.
Some technical experience is required to setup your own instance of the app, but you don't have to write any code. Once setup, it can be used by anyone using a standard Podcast player.

# How does it work?
1. Amazon CloudWatch periodically triggers a function hosted using AWS Lambda.
2. The function checks for new content on the selected RSS feed.
3. When any new text content is available, it is retrieved, converted into lifelike speech using Amazon Polly, and stored as a set of audio files in a chosen S3 bucket.
4. The same S3 bucket that hosts podcast.xml can be pointed to by any Podcast application (like iTunes), in order to play the audio content.

# Setup
## S3
1. Login to your AWS account.
2. Create a new S3 bucket that will be used to store synthesized audio.
    * Go to the bucket properties->Permissions->Add bucket policy and paste the following policy:
    
        ```
        {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "AddPerm",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        }]}
        ```
        Make sure to substitute YOUR_BUCKET_NAME with an arbitrary name, keeping in mind that it has to be globally unique. Save the policy.
    * Expand the "Static Website Hosting" section in the bucket properties, choose "Enable website hosting", type "podcast.xml" in the "Index Document" field, and save the settings.

## Lambda
1. Create a new Lambda function.
2. Choose "Python 2.7" as runtime and "hello-world-python" as a blueprint. 
3. Skip triggerts (just click "Next"); we will get to that later.
4. Choose an arbitrary name for your function, change "Code entry type" to "Upload a .ZIP file", and upload dist/package.zip from this repository.
5. Choose "Create a custom role" in the "Role" field, which will open a new tab.
    * In the newly opened tab, change "IAM Role" to "Create a new IAM Role", and choose an arbitrary name for the role.
    * Expand "View Policy Document", click the "Edit" link, and paste the following content into the text area:
    
        ```
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "polly:SynthesizeSpeech",
                        "s3:ListBucket",
                        "s3:PutObject",
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }
        ```
    * Click the "Allow" button at the bottom of the page, which will close the tab and get you back to the Lambda function settings.
6. Change the Timeout to 5 min 0 seconds.
7. Click "Next", review the settings, and click "Create function".
8. Optional check to prove that the new function works as expected:
    * Click "Test" at the top of the page.
    * Use the following JSON document as test even input:
    
        ```
        {
          "rss": "http://feeds.feedburner.com/AmazonWebServicesBlog", 
          "bucket": "YOUR_BUCKET_NAME"
        }
        ```
        Make sure to substitute YOUR_BUCKET_NAME, and feel free to change rss into any RSS URL.
    * Click "Save and test" and wait until the function is finished. Keep in mind that it may take a while to retrieve, convert and store the content.
    * Go back to your newly created S3 bucket to see if it contains any new content.

## CloudWatch
1. Go to Amazon CloudWatch, which will be used to periodically trigger your lambda function.
    * Go to "Events" and click "Create rule".
    * Select "Schedule" in "Event selector".
    * In the "Targets" section, choose "Lambda function", and then choose the newly created function. Expand "Configure input", choose "Constant (JSON text)", use the following JSON document:
    
        ```
        {
          "rss": "http://feeds.feedburner.com/AmazonWebServicesBlog", 
          "bucket": "YOUR_BUCKET_NAME"
        }
        ```
        That's the same JSON that you used before, to test your function (unless you were brave enough to skip that step). Again, make sure to substitute YOUR_BUCKET_NAME and choose your favorite RSS URL.
2. Click configure details.
3. Choose an arbitrary name and click "Create rule".
4. Go back to your S3 bucket, click on the podcast.xml file that was previously created there, and open "Properties".
5. Copy link and use it in any Podcast player (like iTunes or any Podcast app in Android). Optionally, use any URL shortener (like bit.ly) to create a short version of the link.

 
## Building the zip package on a MAC (easy on Linux)
1. If you upload the Mac version, you’ll see “invalid ELF header” logs when you try to test your Lambda function.
* You need Linux versions of library files to be able to run in AWS Lambda environment. That's where Docker comes in handy. 
* With Docker you can very easily can run a Linux container locally on your Mac, install the Python libraries within the container so they are automatically in the right Linux format, and zip up the files ready to upload to AWS. 
* You’ll need Docker for Mac installed first. (https://www.docker.com/products/docker)

2. Spin up an Ubuntu container which will have the lambda code you want to package
    * run the following command:

        ```
        $ docker run -v <full path directory with your code>:/working -it --rm ubuntu
        ```
        The -v flag makes your code directory available inside the container in a directory called “working”.
        You should now be inside the container at a shell prompt.

3. Install pip and zip.
    * run the following commands:    
        ```
        $ apt-get update
        $ apt-get install python-pip
        $ apt-get install zip
        ```

4. Install the python requirements.
    * run the following commands:    
        ```
        $ cd working
        $ pip install -r requirements.txt -t .vendor
        ```

5. Package your code.
    * run the following commands:
        ```
        $ zip package.zip podcast.py
        $ zip -r package.zip .
        ```

Voila! Your package file is ready to be used in Lambda.

## IMPORTANT
1.  When uploading your package in Lambda, don't forget the enviroment variable "AWS_REGION_BUCKET" which is the region where you created the bucket that will hold the podcast.

## Test with Emulambda
1. install emulambda:
    * run the following commands:
        ```
        pip install git+https://github.com/fugue/emulambda.git
        ```
2. export AWS_REGION_BUCKET="eu-west-1"
3. Test
    * run the following commands:
        ```
        emulambda podcast.handler -v event.json
        ```

## Summary
That's it! Your podcast is ready. Use it on your own, or share the URL with your friends. Optionally publish it as an audio version of your own blog (if you are the content owner).

