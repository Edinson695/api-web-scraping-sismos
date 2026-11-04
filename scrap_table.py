import requests
import boto3
import uuid

def lambda_handler(event, context):
    # Apuntamos directamente a la API JSON oculta del IGP en lugar de la web HTML
    url = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/AAAA"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    # Realizar petición
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code, 
            'body': 'Error al acceder a la API JSON del IGP'
        }

    # Convertir la respuesta HTTP directamente en una lista de diccionarios de Python
    sismos_totales = response.json()
    
    # Slice para extraer únicamente los 10 primeros sismos de la lista
    ultimos_10 = sismos_totales[:10]

    # Conectar a DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping')

    # Eliminar todos los elementos antiguos (Clean up)
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key={'id': each['id']})

    # Guardar los 10 nuevos registros
    for index, sismo in enumerate(ultimos_10, start=1):
        # Convertimos los valores a string para evitar que DynamoDB rechace valores tipo Float
        item = {k: str(v) for k, v in sismo.items()}
        item['#'] = str(index)
        item['id'] = str(uuid.uuid4())
        
        table.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': 'Los 10 ultimos sismos se actualizaron correctamente en DynamoDB'
    }