import datetime


def make_timestamp() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d%H%M%S')


if __name__ == "__main__":
    print(make_timestamp())
