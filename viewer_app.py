from flask import Flask, render_template_string
from datetime import datetime, timedelta, date
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///turnos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo para la base de datos
class CirujanosTurno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    nombre_turno = db.Column(db.String(50), nullable=False)
    cirujano1 = db.Column(db.String(100), nullable=False)
    cirujano2 = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Turno {self.fecha} {self.nombre_turno}>'

# Clases y lógica de la rotativa
class TurnoCiclo:
    def __init__(self, nombre, color, fecha_inicial, semana_inicial):
        self.nombre = nombre
        self.color = color
        self.fecha_inicial = fecha_inicial if isinstance(fecha_inicial, date) else fecha_inicial.date()
        self.semana_inicial = semana_inicial
        self.ciclo_dias = 42  # 6 semanas

    def get_turno_para_fecha(self, fecha):
        fecha = fecha if isinstance(fecha, date) else fecha.date()
        dias_desde_inicio = (fecha - self.fecha_inicial).days
        ciclo_actual = (dias_desde_inicio // self.ciclo_dias)
        dia_en_ciclo = dias_desde_inicio % self.ciclo_dias
        semana_en_ciclo = (dia_en_ciclo // 7 + self.semana_inicial) % 6
        if semana_en_ciclo == 0:
            semana_en_ciclo = 6
        dia_semana = fecha.weekday()
        dia_turno = {
            "Turno lunes": 0,
            "Turno martes": 1,
            "Turno miércoles": 2,
            "Turno jueves": 3
        }[self.nombre]
        if semana_en_ciclo <= 3:
            return dia_semana == dia_turno
        elif semana_en_ciclo == 4:
            return dia_semana == dia_turno or dia_semana == 6
        elif semana_en_ciclo == 5:
            return dia_semana == 5
        else:  # semana_en_ciclo == 6
            return dia_semana == 4

class TurnoVolante:
    def __init__(self, nombre, color, fecha_inicial):
        self.nombre = nombre
        self.color = color
        self.fecha_inicial = fecha_inicial if isinstance(fecha_inicial, date) else fecha_inicial.date()

    def get_turno_para_fecha(self, fecha):
        fecha = fecha if isinstance(fecha, date) else fecha.date()
        if self.nombre == "Volante 1":
            dias_desde_v1 = (fecha - datetime(2025, 1, 3).date()).days
            return dias_desde_v1 >= 0 and dias_desde_v1 % 6 == 0
        else:  # Volante 2
            dias_desde_v2 = (fecha - datetime(2025, 1, 4).date()).days
            return dias_desde_v2 >= 0 and dias_desde_v2 % 6 == 0

# Configuración de turnos con fechas consistentes
TURNOS = {
    "Turno miércoles": TurnoCiclo("Turno miércoles", "#4EBFBFB3", datetime(2025, 1, 1).date(), 3),
    "Turno jueves": TurnoCiclo("Turno jueves", "#4F97A3B3", datetime(2025, 1, 2).date(), 4),
    "Volante 1": TurnoVolante("Volante 1", "#7CC6A6B3", datetime(2025, 1, 3).date()),
    "Volante 2": TurnoVolante("Volante 2", "#006D77B3", datetime(2025, 1, 4).date()),
    "Turno lunes": TurnoCiclo("Turno lunes", "#20B2AAB3", datetime(2025, 1, 6).date(), 2),
    "Turno martes": TurnoCiclo("Turno martes", "#5F9EA0B3", datetime(2025, 1, 7).date(), 3)
}

def get_turno_for_date(fecha, turnos):
    fecha = fecha if isinstance(fecha, date) else fecha.date()
    for turno_name, turno in turnos.items():
        if turno.get_turno_para_fecha(fecha):
            return {"nombre": turno.nombre, "color": turno.color}
    return None

# Diccionario de colores para los turnos
COLORES_TURNOS = {
    "Turno miércoles": "#4EBFBFB3",
    "Turno jueves": "#4F97A3B3",
    "Volante 1": "#7CC6A6B3",
    "Volante 2": "#006D77B3",
    "Turno lunes": "#20B2AAB3",
    "Turno martes": "#5F9EA0B3"
}

def generar_calendario_año(año):
    calendario = {}
    for mes in range(1, 13):
        for dia in range(1, 32):
            try:
                fecha = datetime(año, mes, dia).date()
                turno_db = CirujanosTurno.query.filter_by(fecha=fecha).first()
                if turno_db:
                    calendario[fecha] = {
                        'nombre': turno_db.nombre_turno,
                        'color': COLORES_TURNOS[turno_db.nombre_turno],
                        'cirujanos': [turno_db.cirujano1, turno_db.cirujano2]
                    }
            except ValueError:
                continue
    return calendario

DIAS_POR_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
NOMBRES_MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <title>AgendaQX - Calendario de Turnos</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap\" rel=\"stylesheet\">
    <style>
        :root {
            --primary-color: #4EBFBF;
            --background-color: #F5F5F5;
            --text-color: #333333;
            --shadow-color: rgba(0, 0, 0, 0.1);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Roboto', sans-serif; margin: 0; padding: 20px; background-color: var(--background-color); color: var(--text-color); }
        .main-title { color: var(--primary-color); text-align: center; font-size: 36px; font-weight: 700; margin: 20px 0 5px; text-shadow: 2px 2px 4px var(--shadow-color); }
        .subtitle { color: #666; text-align: center; font-size: 20px; font-weight: 300; margin-bottom: 40px; }
        .calendar-container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        .year-title { text-align: center; font-size: 24px; margin: 30px 0; padding: 15px; background-color: var(--primary-color); color: white; border-radius: 10px; box-shadow: 0 4px 6px var(--shadow-color); }
        .mes { background: white; border-radius: 15px; padding: 25px; margin-bottom: 30px; box-shadow: 0 4px 12px var(--shadow-color); text-align: center; }
        .mes h2 { color: var(--primary-color); margin-bottom: 20px; font-weight: 500; display: inline-block; padding: 8px 20px; border-radius: 8px; background: #f8f8f8; box-shadow: 0 2px 4px var(--shadow-color); }
        .dias-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; text-align: left; }
        .weekday { font-weight: 500; text-align: center; padding: 10px; background-color: #f8f8f8; color: var(--text-color); border-radius: 8px; }
        .dia { min-height: 90px; padding: 8px; border: 1px solid #eee; border-radius: 10px; display: flex; flex-direction: column; align-items: center; font-size: 14px; transition: all 0.3s ease; }
        .turno-info { padding: 8px; border-radius: 8px; width: 100%; margin-top: 5px; transition: all 0.3s ease; color: #333; font-weight: 500; }
        .cirujanos { font-size: 12.5px; margin-top: 4px; text-align: center; color: #333; font-weight: 400; line-height: 1.4; padding: 2px 0; }
        @media (max-width: 768px) { .dias-container { font-size: 12px; } .dia { min-height: 70px; padding: 5px; } .turno-info { padding: 5px; } .cirujanos { font-size: 11px; } }
    </style>
</head>
<body>
    <h1 class=\"main-title\">AgendaQX</h1>
    <h2 class=\"subtitle\">Calendario de Turnos</h2>
    <div class=\"calendar-container\">
        {% for año in [2025, 2026] %}
        <div class=\"year-title\">Calendario {{ año }}</div>
        {% for mes in range(12) %}
        <div class=\"mes\" id=\"mes-{{ año }}-{{ mes+1 }}\">
            <h2>{{ nombres_meses[mes] }}</h2>
            <div class=\"dias-container\">
                {% for dia in [\"Lun\", \"Mar\", \"Mié\", \"Jue\", \"Vie\", \"Sáb\", \"Dom\"] %}
                    <div class=\"weekday\">{{ dia }}</div>
                {% endfor %}
                {% set primer_dia = datetime(año, mes + 1, 1).weekday() %}
                {% for _ in range(primer_dia) %}
                    <div class=\"dia\"></div>
                {% endfor %}
                {% for dia in range(1, dias_por_mes[mes] + 1) %}
                    {% set fecha = datetime(año, mes + 1, dia).date() %}
                    <div class=\"dia\">
                        {{ dia }}
                        {% if fecha in calendarios[año] %}
                            <div class=\"turno-info\" style=\"background-color: {{ calendarios[año][fecha].color }}\">
                                {{ calendarios[año][fecha].nombre }}
                                <div class=\"cirujanos\">
                                    {{ calendarios[año][fecha].cirujanos[0] }}<br>
                                    {{ calendarios[año][fecha].cirujanos[1] }}
                                </div>
                            </div>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
        {% endfor %}
    </div>
    <script>
    window.onload = function() {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;
        const mesActual = document.getElementById(`mes-${year}-${month}`);
        if (mesActual) {
            mesActual.scrollIntoView({ behavior: "smooth", block: "start" });
            mesActual.style.boxShadow = "0 0 20px 5px #4EBFBF";
        }
    };
    </script>
</body>
</html>
"""

@app.route('/')
def show_calendar():
    calendarios = {
        2025: generar_calendario_año(2025),
        2026: generar_calendario_año(2026)
    }
    return render_template_string(
        HTML_TEMPLATE,
        datetime=datetime,
        calendarios=calendarios,
        dias_por_mes=DIAS_POR_MES,
        nombres_meses=NOMBRES_MESES
    )

if __name__ == '__main__':
    app.run(debug=True, port=8082) 