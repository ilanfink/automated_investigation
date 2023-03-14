import boto3
import requests
import re
import json
from thefuzz import fuzz
from thefuzz import process
import os

abstract_api = os.environ['abstract_api']
ipgeo_api_key = os.environ['ipgeo_api_key']
ipstack_api_key = os.environ['ipstack_api_key']
webhook = os.environ['webhook']


def ip_investigate(event, context):
    print(event)
    # ip_full = event['rawQueryString']
    # ip = (ip_full[2:]
    ip = event['queryStringParameters']['ip']
    sent_key = event['queryStringParameters']['access_key']
    # ip = '8.8.8.8'
    print(f'Recieved request for {ip}')
    # req = requests.get('http://ifconfig.me')
    # return req.text
    AbstractIpInfo.abstract_api_pull(ip)
    IpGeoInfo.ipgeo_api_pull(ip)
    IpApiInfo.ip_api_pull(ip)
    get_average_org_score(AbstractIpInfo, IpGeoInfo, IpApiInfo)
    get_average_isp_score(AbstractIpInfo, IpGeoInfo, IpApiInfo)
    x = is_cuda(AbstractIpInfo, IpGeoInfo, IpApiInfo)
    y = make_org_judgement(get_average_org_score(AbstractIpInfo, IpGeoInfo, IpApiInfo))
    z = make_isp_judgement(get_average_isp_score(AbstractIpInfo, IpGeoInfo, IpApiInfo))
    payload = {"test": "testing shit from main"}
    post_message(payload, ip, x, y, z)

    return {
        f"{ip} = IP,\n Is this Barracuda": x, "Is this Org Cloud?": y, "Is this ISP Cloud?": z
    }


class AbstractIpInfo:
    def __init__(self, country_code, ip, org, isp, cuda):  # cuda is a boolean
        self.ip = ip
        self.org = org
        self.isp = isp
        self.org_score = org_score
        self.isp_score = isp_score
        self.cuda = cuda

    def abstract_api_pull(ip):
        url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={abstract_api}&ip_address={ip}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        AbstractIpInfo.isp = data['connection']['isp_name'].lower()
        AbstractIpInfo.org = data['connection']['organization_name'].lower()
        AbstractIpInfo.country_code = data['country_code'].lower()
        # print(AbstractIpInfo.country_code, AbstractIpInfo.isp, AbstractIpInfo.org)


class IpApiInfo:
    def __init__(self, country_code, ip, org, isp, cuda):  # cuda is a boolean
        self.country_code = country_code
        self.ip = ip
        self.org = org
        self.isp = isp
        self.org_score = org_score
        self.isp_score = isp_score
        self.cuda = cuda

    def ip_api_pull(ip):
        url = f'http://ip-api.com/json/{ip}?fields=status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,isp,org,as,asname,reverse,mobile,proxy,hosting,query'
        response = requests.get(url)
        data = response.json()
        IpApiInfo.country_code = data['countryCode'].lower()
        IpApiInfo.isp = data['isp'].lower()
        IpApiInfo.org = data['org'].lower()
        # print(IpApiInfo.country_code, IpApiInfo.isp, IpApiInfo.org)


class IpGeoInfo:
    def __init__(self, country_code, ip, org, isp, cuda):  # cuda is a boolean
        self.country_code = country_code
        self.ip = ip
        self.org = org
        self.isp = isp
        self.org_score = org_score
        self.isp_score = isp_score
        self.cuda = cuda

    def ipgeo_api_pull(ip):
        url = 'https://api.ipgeolocation.io/ipgeo?apiKey=' + ipgeo_api_key + '&ip=' + ip
        response = requests.get(url)
        data = response.json()
        IpGeoInfo.country_code = data['country_code2'].lower()
        IpGeoInfo.isp = data['isp'].lower()
        IpGeoInfo.org = data['organization'].lower()
        # print(IpGeoInfo.country_code, IpGeoInfo.isp, IpGeoInfo.org)


def get_average_org_score(a, b, c):
    cloud = ['amazon', 'amazon.com, inc.', 'google', 'google llc', 'microsoft', 'microsoft corporation']
    for letter in [a, b, c]:
        letter.org_score = process.extractOne(letter.org, cloud)
    overall_org_score = (a.org_score[1] + b.org_score[1] + c.org_score[1]) / 3
    return overall_org_score


def get_average_isp_score(a, b, c):
    cloud = ['amazon', 'amazon.com, inc.', 'google', 'google llc', 'microsoft', 'microsoft corporation']
    for letter in [a, b, c]:
        letter.isp_score = process.extractOne(letter.isp, cloud)
    overall_isp_score = (a.isp_score[1] + b.isp_score[1] + c.isp_score[1]) / 3
    return overall_isp_score


def make_org_judgement(a):
    if a > 90:
        print('based on org, this IP is a cloud IP')
        return True
    if a < 90:
        print('based on org, this IP is not a cloud IP')
        return False


def make_isp_judgement(a):
    if a > 90:
        print('based on isp, this IP is a cloud IP')
        return True
    if a < 90:
        print('based on isp, this IP is not a cloud IP')
        return False


def is_cuda(a, b, c):
    total = 0
    cuda = ['barracuda', 'barracuda networks', 'barracuda inc.', 'barracuda networks inc.']
    for letter in [a, b, c]:
        y = process.extractOne(letter.isp, cuda)
        x = process.extractOne(letter.org, cuda)
        total += x[1] + y[1]

    if (total / 6) > 90:
        print('this IP is a CUDA IP')
        return True
    else:
        print('this IP is not a CUDA IP')
        return False


def post_message(payload, ip, x, y, z):
    # """Post a message to slack using a webhook url."""
    payload = {
        'text': f'IP = {ip} \n\nIs this a Barracuda IP ?: {x}  \n\nIs this a Org a Cloud Provider ?: {y}  \n\nIs this ISP a Cloud Provider ?: {z} '}
    # payload = {'text': f' Is this Barracuda?: {x}  ":eyepatch_morty:"  \n\nIs this Org Cloud?: {y} ":eyepatch_morty:" ":bananadance:" \n\nIs this ISP Cloud?:' {z} ":eyepatch_morty:"}
    return requests.post(webhook, json.dumps(payload))




