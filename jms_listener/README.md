* The following folder structure will be followed.
* The folders will be created as and when required

project/
│
├── app/
│   ├── main.py
│   ├── core/              # config, db, settings
│   ├── api/               # routes (controllers)
│   ├── models/            # ORM models
│   ├── schemas/           # request/response schemas
│   ├── services/          # business logic (IMPORTANT)
│   ├── repositories/      # DB queries
│   ├── events/            # event schema + publisher
│   ├── outbox/            # outbox logic + worker
│   ├── consumers/         # Kafka consumers
│   └── utils/
│
├── scripts/               # cron / workers
├── tests/
├── requirements.txt
└── README.md