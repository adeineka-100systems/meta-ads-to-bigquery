import os
import datetime
from google.cloud import bigquery
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
APP_SECRET = os.environ.get("APP_SECRET")
AD_ACCOUNT_ID = os.environ.get("AD_ACCOUNT_ID", "act_967886028923503")

PROJECT_ID = "budmo-463809"
DATASET_ID = "meta_ads"
TABLE_ID = "meta_ads_insights"

print("Ініціалізація Meta API...")
FacebookAdsApi.init(access_token=ACCESS_TOKEN, app_secret=APP_SECRET)
account = AdAccount(AD_ACCOUNT_ID)

end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=90)

date_preset_params = {
    'time_range': {
        'since': start_date.strftime('%Y-%m-%d'),
        'until': end_date.strftime('%Y-%m-%d')
    },
    'time_increment': 1,
    'level': 'campaign'
}

fields = ['date_start', 'campaign_id', 'campaign_name', 'spend', 'impressions', 'clicks']

print(f"Отримуємо витрати з {start_date} по {end_date}...")
insights = account.get_insights(fields=fields, params=date_preset_params)

rows_to_insert = []
for item in insights:
    rows_to_insert.append({
        "date": item.get('date_start'),
        "campaign_id": str(item.get('campaign_id')),
        "campaign_name": item.get('campaign_name'),
        "spend": float(item.get('spend', 0.0)),
        "impressions": int(item.get('impressions', 0)),
        "clicks": int(item.get('clicks', 0)),
        "updated_at": datetime.datetime.utcnow().isoformat()
    })

print(f"Знайдено {len(rows_to_insert)} рядків. Завантажуємо в BigQuery...")

bq_client = bigquery.Client(project=PROJECT_ID)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

dataset_ref = bq_client.dataset(DATASET_ID)
try:
    bq_client.get_dataset(dataset_ref)
except Exception:
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "EU"
    bq_client.create_dataset(dataset)

job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
)

job = bq_client.load_table_from_json(rows_to_insert, table_ref, job_config=job_config)
job.result()

print(f"УСПІШНО! Таблицю {table_ref} оновлено в BigQuery!")
