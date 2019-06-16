import urllib.request, os, zipfile, boto3, pandas as pd, argparse
from urllib.parse import urlparse
from datetime import datetime as dt


# main function
def main(parameters):
    # links file name
    links_file = "links.txt"

    #path for data
    dir_path="/home/ubuntu/data/"

    if parameters.type == '1':
        print("Batch")
        # URL to use
        initialurl = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
        urllib.request.urlretrieve(initialurl, links_file)
    elif parameters.type == '2':
        print("Live")
        # URL to use
        initialurl = 'http://data.gdeltproject.org/gdeltv2/lastupdate.txt'
        urllib.request.urlretrieve(initialurl, links_file)
    else:
        print("Custom")

    # create a new client to our s3 bucket
    s3 = boto3.client('s3')
    bucket_name = 'nmduartegdelt'

    # reads the links master file that contains all the GDELT links
    df = pd.read_csv(links_file, delimiter=" ", header=None)

    # depending on the number of the columns, we set the headers
    if parameters.columns == '1':
        df.columns = ['url']
    else:
        df.columns = ['id', 'hash', 'url']

    # the initial file has data since 2016, but we are not looking into all files
    # we are just looking for 2019, so we define the start date
    start_date = dt.strptime("20190101", "%Y%m%d")

    for index, row in df.iterrows():
        if row['url'] == row['url']:  # we need to check if it's nan or not
            print(index, row['url'])  # for debug purposes

            # parser so that we can just get the file name
            url_parsed = urlparse(row['url'])
            original_url_file_name = os.path.basename(url_parsed.path)

            # date of the current file to be downloaded
            current_date = dt.strptime(original_url_file_name[:8], "%Y%m%d")

            # check if the file is more recent than our start date
            if current_date > start_date:
                # output file
                final_dir = os.path.join(dir_path, original_url_file_name)
                # downloads the ZIP file
                urllib.request.urlretrieve(row['url'], final_dir)

                # we need to unzip the file
                zip_ref = zipfile.ZipFile(final_dir, 'r')

                # this will be useful to get the extracted file name so that we can delete it after upload
                extracted = zip_ref.namelist()

                # extract the file
                zip_ref.extractall(dir_path)
                zip_ref.close()

                # remove zip file
                os.remove(final_dir)

                # final pathfile for the extracted file
                filename = os.path.join(dir_path, extracted[0])

                # Uploads the file to S3
                # s3.upload_file(filename, bucket_name, 'test/'+extracted[0])
                s3.upload_file(filename, bucket_name, filename)

                # deletes the extracted file
                os.remove(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download gdelt files')

    parser.add_argument('-t', '--type',
                    help='Type of process to run. 1 for batch; 2 for live; 3 for custom', required=True)
    parser.add_argument('-c', '--columns',
                    help='Number of existing columns in the source files', required=True)

    cmd_opts = parser.parse_args()
    main(cmd_opts)
