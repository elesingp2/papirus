# в терминале мака
ssh root@38.180.213.248
BMM7u7nj6V

# в терминале VSCode±!!!!!!!!!!!!!!!!<HUUUUY SPERMA
scp -rv /Users/elesin.gp/Desktop/papirus/app.py root@38.180.213.248:~/papirus

# проверить получилось ли
ls 
# rm -r myprojectenv удалить ненужное

# в терминале мака
cd papirus
python3 -m venv venv
source venv/bin/activate # ctivate
pip install -r requirements.txt



apt install sudo
apt install nginx
sudo apt install ufw
sudo ufw enable
systemctl start nginx
# заходим в браузере на http://38.180.213.248 и должна появиться приветсвенная страница nginx
apt update
#apt install python3-pip python3-venv nginx
pip3 install gunicorn

# база данных
# если нужно удалить: apt-get remove --purge postgresql postgresql-* + apt-get autoremove  удалить зависимости apt-get clean проверить dpkg -l | grep postgresql
apt-get install postgresql postgresql-contrib
systemctl start postgresql
systemctl status postgresql

sudo -u postgres psql
ALTER USER postgres WITH PASSWORD '1234';
\du+
\dp public.* 
CREATE USER root WITH ENCRYPTED PASSWORD '1234';
CREATE DATABASE mydatabase;
CREATE SCHEMA mydatabase;

GRANT ALL PRIVILEGES ON DATABASE mydatabase TO root;
GRANT ALL PRIVILEGES ON SCHEMA mydatabase TO root;
GRANT ALL PRIVILEGES ON SCHEMA public TO root;
GRANT CREATE ON SCHEMA public TO root;
GRANT ALL PRIVILEGES ON SCHEMA mydatabase TO root;

SELECT schema_name, schema_owner
FROM information_schema.schemata
WHERE schema_name = 'public';

ALTER SCHEMA public OWNER TO root;
ALTER DATABASE public OWNER TO root;
\du
\q

flask db init
flask db migrate -m "Initial migration."
flask db upgrade
flask run


nano /etc/nginx/sites-available/default
nano /etc/nginx/sites-available/papirus
server {
    listen 80;
    listen [::]:80;

    server_name papirus.tech;  # Замените на ваш домен или IP-адрес

    location / {
        proxy_pass http://127.0.0.1:8000;  
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
# проверяем синтакси конфигурации
sudo nginx -t

#Создаем символическую ссылку:
sudo ln -s /etc/nginx/sites-available/papirus /etc/nginx/sites-enabled/
systemctl restart nginx

systemctl status nginx

gunicorn --bind 0.0.0.0:8000 wsgi:app & # фоновый режим( nohup в начале = рабоает после закрытия терминалоа)

# как завершить ( процесс с grep gunicorn должен работать )
ps aux | grep gunicorn 
kill 83455

http://0.0.0.1:8000 # локальный запуск
http://38.180.213.248:5000 # глобавльный запуск