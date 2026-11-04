import requests
import boto3
import uuid

def lambda_handler(event, context):
    # Consumimos la API directamente
    url = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/AAAA"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # verify=False permite saltar el bloqueo del certificado SSL en AWS Lambda
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
    except Exception as e:
        return {'statusCode': 500, 'body': f'Error de conexión: {str(e)}'}

    if response.status_code != 200:
        return {
            'statusCode': response.status_code, 
            'body': f'Error en API. Respondió: {response.text[:200]}'
        }

    # Procesar el JSON y tomar solo los 10 primeros
    sismos_totales = response.json()
    ultimos_10 = sismos_totales[:10]

    # Guardar en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping')

    # Limpiar tabla
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key={'id': each['id']})

    # Insertar los 10 sismos
    for index, sismo in enumerate(ultimos_10, start=1):
        item = {k: str(v) for k, v in sismo.items()} # Convertir todo a string por seguridad
        item['#'] = str(index)
        item['id'] = str(uuid.uuid4())
        table.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': ultimos_10
    }