import os
import datetime
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def find_history_dbs():
    browser_data_path = r"AppData\Local\Google\Chrome\User Data\Default"
    history = os.path.join(os.path.expanduser('~'), browser_data_path)
    files = os.listdir(history)

    real_dbs = []
    for file in files:
        if 'History' in file and 'journal' not in file:
            real_dbs.append(os.path.join(history, file))

    return real_dbs


def date_from_webkit(webkit_timestamp):
    epoch_start = datetime.datetime(1601, 1, 1)
    delta = datetime.timedelta(microseconds=int(webkit_timestamp))
    return (epoch_start + delta)


db_files = find_history_dbs()

df = pd.DataFrame()
for db_file in db_files:
    conn = sqlite3.connect(db_file)
    df = pd.concat([df, pd.read_sql('SELECT * FROM urls', conn)])
    conn.close()

# Dataframe сформирован, теперь обработаем его
df.drop_duplicates(inplace=True)

df = df[df['last_visit_time'] != 0]

df.sort_values(by='last_visit_time', inplace=True)

needless_columns = ['visit_count', 'typed_count', 'hidden']
df.drop(needless_columns, axis=1, inplace=True)

df.reset_index(inplace=True)

df['last_visit_time'] = df['last_visit_time'].map(date_from_webkit)


print(len(df))
print(df.columns)
df.info()

# Dataframe обработан, сделаем экспорт и график

os.makedirs('data', exist_ok=True)

events = df['last_visit_time'].tolist()

merged_table_name = 'data/history.xlsx'
df.to_excel(merged_table_name, index=False)

fig, ax = plt.subplots(figsize=(10, 2))

ax.eventplot(events,
             orientation="horizontal",
             colors="green",
             lineoffsets=0,
             linelengths=1.5)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%B"))
plt.xticks(rotation=45)
ax.get_yaxis().set_visible(False)

plt.title("История - даты активности")
plt.tight_layout()

plot_name = 'data/history.pdf'
plt.savefig(plot_name, dpi=300)
