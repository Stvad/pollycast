# Polly podcast
This app allows you to easily convert any publicly available RSS content into audio Podcasts, so you can listen to your favorite blogs on mobile devices instead of reading them.

# Notice
This repo is based on https://github.com/awslabs/amazon-polly-sample but this version actually works.
* The podcast file links are not broken;
* Support for far larger text length
* Support for extracting content from the link provided in RSS feed (I use this to convert my Pocket-saved articles)


# Requirements
You will need an AWS account and an RSS feed.
Some technical experience is required to setup your own instance of the app, but you don't have to write any code. Once setup, it can be used by anyone using a standard Podcast player.

# How does it work?
1. Amazon CloudWatch periodically triggers a function hosted using AWS Lambda.
2. The function checks for new content on the selected RSS feed.
3. When any new text content is available, it is retrieved, converted into lifelike speech using Amazon Polly, and stored as a set of audio files in a chosen S3 bucket.
4. The same S3 bucket that hosts podcast.xml can be pointed to by any Podcast application (like iTunes), in order to play the audio content.

# AWS Resources Setup

All relevant resources are defined in `samTempleate.yaml` file.
So only thing you need to do is to:

1. **TODO**. Collect relevant dependencies.
Section below is kind of relevant, but very moderately.
Very briefly you need to:

* Get all dependencies into some build
  directory (`pipenv run pip install -r <(pipenv lock -r) --target _build/`)
* Add your code there (`cp -Rf pollycast _build/`)
* And point `CodeUri` in `samTempleate.yaml` to your build directory

2.
Run `aws cloudformation package --template-file samTemplate.yaml --s3-bucket <some_s3_bucket_you_have_access_to> > /tmp/packaged.yml`

3.
Run `aws cloudformation deploy --template-file /tmp/packaged.yaml --capabilities CAPABILITY_IAM --parameter-overrides RSSFeed=<link to your rss feed> --stack-name <YOUR STACK NAME>`

 
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
        apt-get update
        apt-get install python3-pip
        apt-get install zip
        pip3 install pipenv
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

