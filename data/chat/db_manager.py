# -*- coding: utf-8 -*-
"""
Chat Database Manager
Manages SQLite database connection and schema for chat sessions
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import uuid
import json
import logging

from models.data_models import PromptTemplate

logger = logging.getLogger(__name__)


class ChatDatabaseManager:
    """
    Manage chat database connection and schema

    Features:
    - Automatic schema initialization
    - Connection management
    - Thread-safe row factory
    """

    def __init__(self, db_path: str = "data/chat/chat.db"):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self):
        """
        Connect to database and initialize schema

        Creates database file if not exists and executes schema.sql
        """
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            # Use Row factory for dictionary-like access
            self.connection.row_factory = sqlite3.Row

            # Enable foreign key constraints (required for CASCADE DELETE)
            self.connection.execute("PRAGMA foreign_keys = ON")

            logger.info(f"Connected to database: {self.db_path}")

            # Initialize schema
            self._initialize_schema()

        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def _initialize_schema(self):
        """
        Create tables if not exist

        Reads and executes schema.sql from the same directory
        """
        try:
            schema_path = Path(__file__).parent / 'schema.sql'

            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            self.connection.executescript(schema_sql)
            self.connection.commit()

            logger.info("Database schema initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Schema initialization error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading schema file: {e}")
            raise

    def close(self):
        """
        Close database connection
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def execute(self, sql: str, parameters: tuple = ()):
        """
        Execute SQL query

        Args:
            sql: SQL statement
            parameters: Query parameters

        Returns:
            Cursor object
        """
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, parameters)
            self.connection.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"SQL execution error: {e}\nSQL: {sql}")
            raise

    def fetchall(self, sql: str, parameters: tuple = ()):
        """
        Execute query and fetch all results

        Args:
            sql: SQL SELECT statement
            parameters: Query parameters

        Returns:
            List of Row objects
        """
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, parameters)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Query error: {e}\nSQL: {sql}")
            raise

    def fetchone(self, sql: str, parameters: tuple = ()):
        """
        Execute query and fetch one result

        Args:
            sql: SQL SELECT statement
            parameters: Query parameters

        Returns:
            Row object or None
        """
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, parameters)
            return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Query error: {e}\nSQL: {sql}")
            raise

    # ==================== 会话管理 (Session CRUD) ====================

    def create_session(self, title: str, settings_json: str = "{}") -> str:
        """
        创建新会话

        Args:
            title: 会话标题（从第一条消息提取，最多10字符）
            settings_json: AI参数设置的JSON字符串

        Returns:
            session_id: 新创建的会话ID (UUID)
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        sql = """
        INSERT INTO sessions (id, title, created_at, updated_at, settings_json)
        VALUES (?, ?, ?, ?, ?)
        """
        self.execute(sql, (session_id, title, now, now, settings_json))

        logger.info(f"会话已创建: {session_id}, 标题: {title}")
        return session_id

    def load_session(self, session_id: str) -> Optional[Dict]:
        """
        加载会话详情

        Args:
            session_id: 会话ID

        Returns:
            会话数据字典，不存在时返回None
            格式: {
                'id': str,
                'title': str,
                'created_at': str,
                'updated_at': str,
                'settings_json': str
            }
        """
        sql = "SELECT * FROM sessions WHERE id = ?"
        row = self.fetchone(sql, (session_id,))

        if row:
            return {
                'id': row['id'],
                'title': row['title'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'settings_json': row['settings_json']
            }
        return None

    def update_session_title(self, session_id: str, title: str):
        """
        更新会话标题

        Args:
            session_id: 会话ID
            title: 新标题（前10字符）
        """
        now = datetime.now().isoformat()
        sql = "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?"
        self.execute(sql, (title, now, session_id))
        logger.info(f"会话标题已更新: {session_id} -> {title}")

    def delete_session(self, session_id: str):
        """
        删除会话（级联删除所有消息）

        Args:
            session_id: 会话ID

        Note:
            外键约束 ON DELETE CASCADE 会自动删除关联的messages
        """
        sql = "DELETE FROM sessions WHERE id = ?"
        self.execute(sql, (session_id,))
        logger.info(f"会话已删除: {session_id}")

    def list_sessions(self, limit: int = 100) -> List[Dict]:
        """
        列出所有会话（按更新时间倒序）

        Args:
            limit: 最大返回数量

        Returns:
            会话列表，每项格式:
            {
                'id': str,
                'title': str,
                'created_at': str,
                'updated_at': str,
                'settings_json': str
            }
        """
        sql = """
        SELECT * FROM sessions
        ORDER BY updated_at DESC
        LIMIT ?
        """
        rows = self.fetchall(sql, (limit,))

        sessions = []
        for row in rows:
            sessions.append({
                'id': row['id'],
                'title': row['title'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'settings_json': row['settings_json']
            })

        logger.debug(f"已加载 {len(sessions)} 个会话")
        return sessions

    # ==================== 提示词管理 ====================

    def get_session_prompt(self, session_id: str) -> Optional[PromptTemplate]:
        """获取会话提示词"""
        sql = """
        SELECT group_name, title, content, updated_at
        FROM session_prompts
        WHERE session_id = ?
        """
        row = self.fetchone(sql, (session_id,))
        if not row:
            return None
        return PromptTemplate.from_dict(
            {
                "group_name": row["group_name"],
                "title": row["title"],
                "content": row["content"],
                "updated_at": row["updated_at"],
            }
        )

    def save_session_prompt(self, session_id: str, prompt: PromptTemplate) -> None:
        """保存会话提示词（存在则更新），并记录历史版本"""
        existing = self.get_session_prompt(session_id)

        if existing and (
            existing.content != prompt.content
            or existing.title != prompt.title
            or existing.group_name != prompt.group_name
        ):
            try:
                next_version = self._get_next_prompt_history_version(session_id)
                history_sql = """
                INSERT INTO session_prompt_history (session_id, version, group_name, title, content, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                self.execute(
                    history_sql,
                    (
                        session_id,
                        next_version,
                        existing.group_name,
                        existing.title,
                        existing.content,
                        existing.updated_at.isoformat(),
                    ),
                )
            except Exception as e:
                logger.error(f"保存提示词历史失败: {e}")

        sql = """
        INSERT INTO session_prompts (session_id, group_name, title, content, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(session_id)
        DO UPDATE SET
            group_name = excluded.group_name,
            title = excluded.title,
            content = excluded.content,
            updated_at = excluded.updated_at
        """
        self.execute(
            sql,
            (
                session_id,
                prompt.group_name,
                prompt.title,
                prompt.content,
                prompt.updated_at.isoformat(),
            ),
        )

    def get_session_prompt_history(self, session_id: str, limit: int = 5) -> List[PromptTemplate]:
        """获取会话提示词历史（按时间倒序）"""
        sql = """
        SELECT group_name, title, content, updated_at
        FROM session_prompt_history
        WHERE session_id = ?
        ORDER BY version DESC
        LIMIT ?
        """
        rows = self.fetchall(sql, (session_id, limit))
        history = []
        for row in rows:
            history.append(
                PromptTemplate.from_dict(
                    {
                        "group_name": row["group_name"],
                        "title": row["title"],
                        "content": row["content"],
                        "updated_at": row["updated_at"],
                    }
                )
            )
        return history

    def _get_next_prompt_history_version(self, session_id: str) -> int:
        """获取下一历史版本号"""
        sql = """
        SELECT COALESCE(MAX(version), 0) AS version
        FROM session_prompt_history
        WHERE session_id = ?
        """
        row = self.fetchone(sql, (session_id,))
        current_version = row["version"] if row and row["version"] else 0
        return current_version + 1

    def cleanup_old_sessions(self, days: int = 90) -> int:
        """
        清理指定天数前的旧会话

        Args:
            days: 保留天数（默认90天）

        Returns:
            删除的会话数量
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # 先查询要删除的会话数量
        count_sql = "SELECT COUNT(*) as count FROM sessions WHERE created_at < ?"
        result = self.fetchone(count_sql, (cutoff_date,))
        count = result['count'] if result else 0

        if count > 0:
            # 删除旧会话（级联删除消息）
            delete_sql = "DELETE FROM sessions WHERE created_at < ?"
            self.execute(delete_sql, (cutoff_date,))
            logger.info(f"已清理 {count} 个旧会话（{days}天前）")

        return count

    # ==================== 消息管理 (Message CRUD) ====================

    def _normalize_metadata(self, metadata: Union[str, Dict[str, Any], None]) -> str:
        """将 metadata 统一转换为 JSON 字符串。"""
        if metadata is None:
            return "{}"
        if isinstance(metadata, str):
            metadata = metadata.strip()
            return metadata or "{}"
        try:
            return json.dumps(metadata, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            logger.warning(f"序列化 metadata 失败: {exc}")
            return "{}"

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata_json: Union[str, Dict[str, Any], None] = None
    ) -> str:
        """
        保存消息到数据库

        Args:
            session_id: 所属会话ID
            role: 消息角色 ('user' | 'assistant')
            content: 消息内容
            metadata_json: 元数据JSON字符串（可选）

        Returns:
            message_id: 新创建的消息ID (UUID)
        """
        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        metadata_str = self._normalize_metadata(metadata_json)

        sql = """
        INSERT INTO messages (id, session_id, role, content, timestamp, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (message_id, session_id, role, content, now, metadata_str))

        # 更新会话的 updated_at 时间
        self.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id)
        )

        logger.debug(f"消息已保存: {message_id}, 角色: {role}, 长度: {len(content)}")
        return message_id

    def load_messages(self, session_id: str) -> List[Dict]:
        """
        加载会话的所有消息（按时间正序）

        Args:
            session_id: 会话ID

        Returns:
            消息列表，每项格式:
            {
                'id': str,
                'session_id': str,
                'role': str,
                'content': str,
                'timestamp': str,
                'metadata_json': str
            }
        """
        sql = """
        SELECT * FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
        """
        rows = self.fetchall(sql, (session_id,))

        messages = []
        for row in rows:
            metadata_raw = row['metadata_json']
            metadata = {}
            if metadata_raw:
                if isinstance(metadata_raw, str):
                    try:
                        metadata = json.loads(metadata_raw) if metadata_raw else {}
                    except json.JSONDecodeError as exc:
                        logger.warning(f"解析消息 metadata 失败: {exc}")
                        metadata = {}
                elif isinstance(metadata_raw, dict):
                    metadata = metadata_raw
            else:
                metadata_raw = "{}"

            messages.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'role': row['role'],
                'content': row['content'],
                'timestamp': row['timestamp'],
                'metadata_json': metadata_raw,
                'metadata': metadata
            })

        logger.debug(f"已加载 {len(messages)} 条消息（会话: {session_id}）")
        return messages

    def delete_messages_by_session(self, session_id: str):
        """
        删除会话的所有消息

        Args:
            session_id: 会话ID

        Note:
            此方法由外键级联删除自动触发，通常不需要手动调用
        """
        sql = "DELETE FROM messages WHERE session_id = ?"
        self.execute(sql, (session_id,))
        logger.debug(f"会话消息已删除: {session_id}")

    # ==================== 搜索功能 (FTS5) ====================

    def search_messages(self, query: str, limit: int = 50) -> List[Dict]:
        """
        全文搜索消息内容

        Args:
            query: 搜索关键词
            limit: 最大返回数量

        Returns:
            消息列表（包含会话信息）
        """
        sql = """
        SELECT m.*, s.title as session_title
        FROM messages m
        JOIN messages_fts fts ON m.rowid = fts.rowid
        JOIN sessions s ON m.session_id = s.id
        WHERE messages_fts MATCH ?
        ORDER BY m.timestamp DESC
        LIMIT ?
        """
        rows = self.fetchall(sql, (query, limit))

        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'session_title': row['session_title'],
                'role': row['role'],
                'content': row['content'],
                'timestamp': row['timestamp']
            })

        logger.debug(f"搜索 '{query}' 找到 {len(results)} 条消息")
        return results

    # ==================== 数据迁移 ====================

    def migrate_from_json(self, json_file_path: str) -> bool:
        """
        从旧的JSON格式迁移数据到SQLite

        Args:
            json_file_path: JSON文件路径（如 .cache/chat_state.json）

        Returns:
            是否迁移成功
        """
        try:
            json_path = Path(json_file_path)
            if not json_path.exists():
                logger.info(f"JSON文件不存在，跳过迁移: {json_file_path}")
                return False

            with open(json_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 提取会话信息
            session_id = state.get('session_id', str(uuid.uuid4()))
            messages = state.get('messages', [])

            if not messages:
                logger.info("JSON文件中无消息，跳过迁移")
                return False

            # 生成会话标题（从第一条用户消息）
            first_user_msg = next((m for m in messages if m.get('role') == 'user'), None)
            title = "迁移的会话"
            if first_user_msg:
                content = first_user_msg.get('content', '')
                title = content[:10] if content else "迁移的会话"

            # 创建会话（获取新生成的session_id）
            new_session_id = self.create_session(title, settings_json="{}")

            # 保存所有消息（使用新的session_id）
            for msg in messages:
                self.save_message(
                    session_id=new_session_id,
                    role=msg.get('role', 'user'),
                    content=msg.get('content', '')
                )

            # 重命名JSON文件为 .migrated
            migrated_path = json_path.with_suffix('.json.migrated')
            json_path.rename(migrated_path)

            logger.info(f"成功迁移 {len(messages)} 条消息到会话 {new_session_id}")
            return True

        except Exception as e:
            logger.error(f"JSON迁移失败: {e}")
            return False
