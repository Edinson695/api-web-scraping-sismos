import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/productos/reportes-sismicos"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # verify=False omite errores de certificados de seguridad
    response = requests.get(url, headers=headers, verify=False, timeout=15)
    
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': f'Fallo de conexión. IGP respondió: {response.text[:300]}'
        }

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    
    if not table:
        return {
            'statusCode': 404,
            'body': f'No hay tabla. HTML recibido: {response.text[:300]}'
        }

    headers_list = [header.text for header in table.find_all('th')]
    rows = []
    for row in table.find_all('tr')[1:11]:  # Límite de 10 sismos
        cells = row.find_all('td')
        rows.append({headers_list[i+1]: cell.text for i, cell in enumerate(cells)})

    # Guardar en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table_db = dynamodb.Table('TablaWebScrapping')
    
    with table_db.batch_writer() as batch:
        for each in table_db.scan()['Items']:
            batch.delete_item(Key={'id': each['id']})

    for index, row in enumerate(rows, start=1):
        row['#'] = str(index)
        row['id'] = str(uuid.uuid4())
        table_db.put_item(Item=row)

    return {'statusCode': 200, 'body': rows}