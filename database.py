import mysql.connector
from typing import Dict, Any, Optional, List, Union
import json
from datetime import datetime, timedelta
import logging
import os

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

current_date = datetime.now().strftime("%Y-%m-%d")
log_file = f"{log_dir}/database_{current_date}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, host: str = "localhost", user: str = "root", password: str = "", database: str = "tg_bot"):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.init_db()

    def init_db(self):
        """Инициализация базы данных и создание необходимых таблиц"""
        try:
            conn = mysql.connector.connect(**self.config)
            c = conn.cursor()
            
            # Создаем таблицу для хранения состояния пользователей
            c.execute('''
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id BIGINT PRIMARY KEY,
                    lang VARCHAR(2),
                    step INT DEFAULT 0,
                    scores JSON DEFAULT ('{"A": 0, "B": 0, "C": 0}'),
                    waiting_for_contact BOOLEAN DEFAULT FALSE,
                    contact_info JSON,
                    offer_scheduled_at TIMESTAMP NULL,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу для логов действий
            c.execute('''
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    action_type VARCHAR(50),
                    details JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_states(user_id) ON DELETE CASCADE
                )
            ''')
            
            # Создаем индексы если они не существуют
            for index, column in [('idx_lang', 'lang'), 
                                ('idx_step', 'step'),
                                ('idx_last_interaction', 'last_interaction')]:
                c.execute(f"SHOW INDEX FROM user_states WHERE Key_name = '{index}'")
                if not c.fetchone():
                    c.execute(f'CREATE INDEX {index} ON user_states ({column})')
            
            conn.commit()
            logger.info("База данных успешно инициализирована")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
            raise
        finally:
            if conn.is_connected():
                conn.close()

    def get_connection(self):
        """Получение соединения с базой данных с обработкой ошибок"""
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as e:
            logger.error(f"Ошибка подключения к базе данных: {str(e)}")
            raise

    def get_user_state(self, user_id: int) -> Dict[str, Any]:
        """Получение состояния пользователя из базы данных"""
        try:
            conn = self.get_connection()
            c = conn.cursor(dictionary=True)
            
            c.execute('''
                SELECT lang, step, scores, waiting_for_contact, contact_info, offer_scheduled_at 
                FROM user_states 
                WHERE user_id = %s
            ''', (user_id,))
            result = c.fetchone()
            
            if result:
                state = {
                    'lang': result['lang'],
                    'step': result['step'],
                    'scores': json.loads(result['scores']) if result['scores'] else {'A': 0, 'B': 0, 'C': 0},
                    'waiting_for_contact': bool(result['waiting_for_contact']),
                    'contact_info': json.loads(result['contact_info']) if result['contact_info'] else None,
                    'offer_scheduled_at': result['offer_scheduled_at']
                }
                logger.debug(f"Получено состояние для user_id {user_id}: {state}")
                return state
            return self._get_default_state()
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении состояния пользователя {user_id}: {str(e)}")
            return self._get_default_state()
        finally:
            if conn.is_connected():
                conn.close()

    def _get_default_state(self) -> Dict[str, Any]:
        """Возвращает состояние по умолчанию"""
        return {
            'lang': None,
            'step': 0,
            'scores': {'A': 0, 'B': 0, 'C': 0},
            'waiting_for_contact': False,
            'contact_info': None,
            'offer_scheduled_at': None
        }

    def save_user_state(self, user_id: int, state: Dict[str, Any]) -> bool:
        """Сохранение состояния пользователя в базу данных"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            contact_info_json = json.dumps(state.get('contact_info')) if state.get('contact_info') else None
            logger.debug(f"Сохранение состояния для user_id {user_id}: contact_info={contact_info_json}")
            
            c.execute('''
                INSERT INTO user_states 
                (user_id, lang, step, scores, waiting_for_contact, contact_info, offer_scheduled_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                lang = VALUES(lang),
                step = VALUES(step),
                scores = VALUES(scores),
                waiting_for_contact = VALUES(waiting_for_contact),
                contact_info = VALUES(contact_info),
                offer_scheduled_at = VALUES(offer_scheduled_at),
                last_interaction = CURRENT_TIMESTAMP
            ''', (
                user_id,
                state.get('lang'),
                state.get('step', 0),
                json.dumps(state.get('scores', {'A': 0, 'B': 0, 'C': 0})),
                state.get('waiting_for_contact', False),
                contact_info_json,
                state.get('offer_scheduled_at')
            ))
            
            conn.commit()
            logger.info(f"Состояние для user_id {user_id} успешно сохранено")
            return True
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при сохранении состояния пользователя {user_id}: {str(e)}")
            return False
        finally:
            if conn.is_connected():
                conn.close()

    def save_contact_info(self, user_id: int, contact_info: Dict[str, Any]) -> bool:
        """Сохранение контактной информации пользователя"""
        try:
            conn = self.get_connection()
            c = conn.cursor()

            contact_info_json = json.dumps(contact_info)
            logger.debug(f"Сохранение contact_info для user_id {user_id}: {contact_info_json}")

            c.execute('''
                UPDATE user_states
                SET contact_info = %s,
                    waiting_for_contact = FALSE
                WHERE user_id = %s
            ''', (
                contact_info_json,
                user_id
            ))

            conn.commit()
            logger.info(f"Контактная информация для user_id {user_id} успешно сохранена")
            return True
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при сохранении контактной информации пользователя {user_id}: {str(e)}")
            return False
        finally:
            if conn.is_connected():
                conn.close()

    def get_contact_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение контактной информации пользователя"""
        try:
            conn = self.get_connection()
            c = conn.cursor(dictionary=True)
            
            c.execute('SELECT contact_info FROM user_states WHERE user_id = %s', (user_id,))
            result = c.fetchone()
            
            if result and result['contact_info']:
                contact_info = json.loads(result['contact_info'])
                logger.debug(f"Получена контактная информация для user_id {user_id}: {contact_info}")
                return contact_info
            logger.warning(f"Контактная информация для user_id {user_id} не найдена")
            return None
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении контактной информации пользователя {user_id}: {str(e)}")
            return None
        finally:
            if conn.is_connected():
                conn.close()

    def clear_offer_schedule(self, user_id: int) -> bool:
        """Очистка запланированного оффера для пользователя"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            c.execute('''
                UPDATE user_states
                SET offer_scheduled_at = NULL
                WHERE user_id = %s
            ''', (user_id,))
            
            conn.commit()
            logger.info(f"Оффер очищен для user_id {user_id}")
            return True
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при очистке оффера пользователя {user_id}: {str(e)}")
            return False
        finally:
            if conn.is_connected():
                conn.close()

    def get_all_users(self) -> Dict[int, Dict[str, Any]]:
        """Получение всех пользователей из базы данных"""
        try:
            conn = self.get_connection()
            c = conn.cursor(dictionary=True)
            
            c.execute('''
                SELECT user_id, lang, step, scores, waiting_for_contact, 
                       contact_info, offer_scheduled_at, last_interaction
                FROM user_states
            ''')
            
            users = {}
            for result in c.fetchall():
                users[result['user_id']] = {
                    'lang': result['lang'],
                    'step': result['step'],
                    'scores': json.loads(result['scores']) if result['scores'] else {'A': 0, 'B': 0, 'C': 0},
                    'waiting_for_contact': bool(result['waiting_for_contact']),
                    'contact_info': json.loads(result['contact_info']) if result['contact_info'] else None,
                    'offer_scheduled_at': result['offer_scheduled_at'],
                    'last_interaction': result['last_interaction']
                }
            logger.info(f"Получено {len(users)} пользователей из базы")
            return users
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении всех пользователей: {str(e)}")
            return {}
        finally:
            if conn.is_connected():
                conn.close()

    def cleanup_old_records(self, days: int = 30) -> int:
        """Очистка старых записей"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Сначала удаляем связанные записи в логах
            c.execute('''
                DELETE FROM action_logs 
                WHERE user_id IN (
                    SELECT user_id FROM user_states 
                    WHERE last_interaction < %s
                )
            ''', (cutoff_date,))
            
            # Затем удаляем самих пользователей
            c.execute('DELETE FROM user_states WHERE last_interaction < %s', (cutoff_date,))
            
            affected_rows = c.rowcount
            conn.commit()
            logger.info(f"Удалено {affected_rows} старых записей")
            return affected_rows
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при очистке старых записей: {str(e)}")
            return 0
        finally:
            if conn.is_connected():
                conn.close()

    def log_action(self, user_id: int, action_type: str, details: Optional[Dict] = None) -> bool:
        """Логирование действия пользователя"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO action_logs 
                (user_id, action_type, details)
                VALUES (%s, %s, %s)
            ''', (
                user_id,
                action_type,
                json.dumps(details) if details else None
            ))
            
            conn.commit()
            logger.info(f"Действие '{action_type}' для user_id {user_id} залогировано")
            return True
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при логировании действия пользователя {user_id}: {str(e)}")
            return False
        finally:
            if conn.is_connected():
                conn.close()

    def get_user_actions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение действий пользователя"""
        try:
            conn = self.get_connection()
            c = conn.cursor(dictionary=True)
            
            c.execute('''
                SELECT action_type, details, created_at
                FROM action_logs
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ''', (user_id, limit))
            
            actions = []
            for result in c.fetchall():
                actions.append({
                    'action_type': result['action_type'],
                    'details': json.loads(result['details']) if result['details'] else None,
                    'created_at': result['created_at']
                })
            logger.info(f"Получено {len(actions)} действий для user_id {user_id}")
            return actions
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении действий пользователя {user_id}: {str(e)}")
            return []
        finally:
            if conn.is_connected():
                conn.close()