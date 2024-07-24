# web_chat
Клиент/серверное приложения для обмена сообщениями между клиентами. 
- ЯП Python >= 3.8, asyncio для сетевого программирования 
- Протокол TCP
- Формат сообщений JSON

Проверено на Win11 Python3.12

## Запуск
cd web_chat  
python client.py  
python server.py  

### Переменные окружения
Находятся в файле .env
Извлекаются для дальнейшего использования функцией, объявленной в /common/env.py

### Доступные команды
        - connect           : connect to a server
        - disconnect        : disconnect from the server
        - send <message>    : send a message to the server
        - set_name <name>   : set the client's name
        - get_name          : get the client's name
        - help              : get 'help' text
        - quit              : quit the application
  

## Комментарии
1. Не знаю, опечатка ли, но в шаблонах сообщений из условий в некоторых местах для пользователя использован ключ 'login', а где-то 'user' - (использовал везде 'login').
2. Есть ограничение на длину сообщения: все в целом должно помещаться в считываемый блок (да, можно было в цикле его собрать, но тогда нужно однозначно определять символ окончания сообщения: /n не совсем подходит, а остальное может встречаться в тексте сообщения).
3. Уже ближе к концу прочел про asyncio.Protocol, возможно, было бы лучше наследоваться от него.
4. Не уверен, что используемое решение для обхода блокировки консоли input-ом оптимально.
