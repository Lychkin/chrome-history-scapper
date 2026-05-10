import os
import datetime
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import calplot


def find_history_dbs():
    browser_data_path = r"AppData\Local\Google\Chrome\User Data\Default"
    history = os.path.join(os.path.expanduser("~"), browser_data_path)
    files = os.listdir(history)

    real_dbs = []
    for file in files:
        if "History" in file and "journal" not in file:
            real_dbs.append(os.path.join(history, file))

    return real_dbs


def date_from_webkit(webkit_timestamp):
    epoch_start = datetime.datetime(1601, 1, 1)
    delta = datetime.timedelta(microseconds=int(webkit_timestamp))
    return epoch_start + delta


db_files = find_history_dbs()

df = pd.DataFrame()
for db_file in db_files:
    print(f"Connecting to {db_file}...")
    conn = sqlite3.connect(db_file)
    df = pd.concat([df, pd.read_sql("SELECT * FROM urls", conn)])
    conn.close()

# Dataframe сформирован, теперь обработаем его
print("Entries before proccesing: ", len(df))
df.drop_duplicates(inplace=True)

df = df[df["last_visit_time"] != 0]

df.sort_values(by="last_visit_time", inplace=True)

needless_columns = ["visit_count", "typed_count", "hidden"]
df.drop(needless_columns, axis=1, inplace=True)

df.reset_index(inplace=True)

df["last_visit_time"] = df["last_visit_time"].map(date_from_webkit)


print("Entries after proccesing: ", len(df))
df.info()

# Dataframe обработан, сделаем экспорт в таблицу Excel и график

os.makedirs("data", exist_ok=True)

now = datetime.datetime.now().strftime("%d-%m-%y %H-%M-%S")

# Экспорт в Excel-таблицу
merged_table_name = f"data/history_{now}.xlsx"
df.to_excel(merged_table_name, index=False)
print("Export to Excel - done")

# Экспорт в график внутри Pdf-файла
df_dates = df[["last_visit_time"]].copy()
df_dates["last_visit_time"] = df_dates["last_visit_time"].dt.normalize()
df_dates = (
    df_dates.groupby(df["last_visit_time"].dt.normalize())
    .size()
    .reset_index(name="count")
)

df_dates = df_dates.set_index("last_visit_time")
data = df_dates["count"]

calplot.calplot(
    data,
    cmap="YlGnBu",
    figsize=(16, 10),
    yearlabel_kws={"fontname": "Arial", "fontsize": 18},
    subplot_kws={"title": ""},
    suptitle="Calendar Heatmap по годам",
)

plot_name = f"data/history_{now}.pdf"
plt.savefig(plot_name, dpi=300)

print("Export to PDF - done")
