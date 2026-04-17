"""
SQLite 数据库管理模块
"""
import sqlite3
import os
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from .models import DetectionRecord, User

# 项目根目录（database/ 的上级），保证路径不受 QFileDialog 改变 CWD 影响
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "history.db"):
        if os.path.isabs(db_path):
            self.db_path = db_path
        else:
            self.db_path = os.path.join(_PROJECT_ROOT, db_path)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_record(row) -> DetectionRecord:
        return DetectionRecord(
            id=row['id'],
            timestamp=row['timestamp'],
            type=row['type'],
            source=row['source'],
            model_name=row['model_name'],
            total_objects=row['total_objects'],
            class_distribution=row['class_distribution'],
            details=row['details'],
            latitude=row['latitude'] if 'latitude' in row.keys() else None,
            longitude=row['longitude'] if 'longitude' in row.keys() else None,
        )

    def _init_database(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT NOT NULL,
                source TEXT,
                model_name TEXT,
                total_objects INTEGER DEFAULT 0,
                class_distribution TEXT,
                details TEXT,
                latitude REAL,
                longitude REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 迁移：为旧表添加 GPS 列
        cursor.execute("PRAGMA table_info(detection_history)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'latitude' not in columns:
            cursor.execute("ALTER TABLE detection_history ADD COLUMN latitude REAL")
        if 'longitude' not in columns:
            cursor.execute("ALTER TABLE detection_history ADD COLUMN longitude REAL")

        # 预置管理员账号
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ('admin', 'admin123', 'admin')
            )

        conn.commit()
        conn.close()

    def add_record(self, record: DetectionRecord) -> int:
        """添加检测记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO detection_history
            (timestamp, type, source, model_name, total_objects, class_distribution, details, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.timestamp,
            record.type,
            record.source,
            record.model_name,
            record.total_objects,
            record.class_distribution,
            record.details,
            record.latitude,
            record.longitude
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id

    def get_all_records(self, limit: int = 1000) -> List[DetectionRecord]:
        """获取所有检测记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM detection_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        records = [self._row_to_record(row) for row in rows]
        return records

    def search_records(self, keyword: str = "", record_type: str = "all") -> List[DetectionRecord]:
        """搜索检测记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM detection_history WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND (source LIKE ? OR model_name LIKE ? OR class_distribution LIKE ?)"
            keyword_pattern = f"%{keyword}%"
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
        if record_type != "all":
            query += " AND type = ?"
            params.append(record_type)
        
        query += " ORDER BY id DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_record(row) for row in rows]

    def get_record_by_id(self, record_id: int) -> Optional[DetectionRecord]:
        """根据ID获取记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM detection_history WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_record(row)
        return None

    def delete_record(self, record_id: int) -> bool:
        """删除指定记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM detection_history WHERE id = ?", (record_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted

    def clear_all_records(self) -> int:
        """清空所有记录，返回删除的数量"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM detection_history")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM detection_history")
        
        conn.commit()
        conn.close()
        
        return count

    def get_records_count(self) -> int:
        """获取记录总数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM detection_history")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

    def get_records_with_gps(self) -> List[DetectionRecord]:
        """获取所有带 GPS 坐标的记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM detection_history
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_record(row) for row in rows]

    def export_to_csv(self, records: List[DetectionRecord], csv_path: str):
        """导出记录到CSV文件"""
        import csv
        
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', '检测时间', '类型', '来源', '模型名称', '目标总数', '类别分布', '详细结果'])
            
            for record in records:
                writer.writerow([
                    record.id,
                    record.timestamp,
                    record.type,
                    record.source,
                    record.model_name,
                    record.total_objects,
                    record.class_distribution,
                    record.details
                ])

    # ── 用户管理 ──

    def user_exists(self, username: str) -> bool:
        """检查用户名是否已存在"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        return exists

    def verify_user(self, username: str, password: str) -> Optional[User]:
        """验证用户登录，成功返回 User 对象，失败返回 None"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                password=row['password'],
                role=row['role'],
                create_time=row['create_time']
            )
        return None

    def register_user(self, username: str, password: str) -> Tuple[bool, str]:
        """注册新用户，返回 (成功与否, 提示信息)"""
        if not username or not password:
            return False, '用户名和密码不能为空'
        if len(username) < 3:
            return False, '用户名至少3个字符'
        if len(password) < 6:
            return False, '密码至少6个字符'
        if self.user_exists(username):
            return False, '用户名已存在'
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, 'user')
            )
            conn.commit()
            conn.close()
            return True, '注册成功'
        except Exception as e:
            return False, f'注册失败: {e}'