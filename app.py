import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pymongo import MongoClient

# ---------------------------------
# CONFIGURACIÓN Y CONEXIÓN
# ---------------------------------
st.set_page_config(page_title="Snake Scoreboard", layout="centered")

@st.cache_resource
def init_connection():
    # Se conecta al contenedor 'mongo' configurado en Docker Compose
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    return MongoClient(uri)

client = init_connection()
db = client[os.getenv("MONGO_DB", "snake_db")]
scores_collection = db["scores"]

# ---------------------------------
# INTERFAZ (UI)
# ---------------------------------
st.title("🐍 Streamlit Snake & MongoDB")

tab1, tab2 = st.tabs(["🎮 Jugar", "🏆 Tabla de Puntuaciones"])

with tab1:
    st.write("Usa las flechas de tu teclado para jugar. Al perder, anota tu puntuación y guárdala.")

    # Inyección de código HTML/JS para el juego en tiempo real
    snake_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        canvas { background: #222; display: block; margin: 0 auto; border-radius: 8px; border: 2px solid #4CAF50;}
      </style>
    </head>
    <body>
    <canvas id="game" width="400" height="400"></canvas>
    <script>
    var canvas = document.getElementById('game');
    var context = canvas.getContext('2d');
    var grid = 16;
    var count = 0;
    var score = 0;
    var snake = { x: 160, y: 160, dx: grid, dy: 0, cells: [], maxCells: 4 };
    var apple = { x: 320, y: 320 };

    function getRandomInt(min, max) { return Math.floor(Math.random() * (max - min)) + min; }

    function loop() {
      requestAnimationFrame(loop);
      if (++count < 6) { return; } // Controla la velocidad del juego
      count = 0;
      context.clearRect(0,0,canvas.width,canvas.height);

      snake.x += snake.dx;
      snake.y += snake.dy;

      // Atravesar paredes
      if (snake.x < 0) { snake.x = canvas.width - grid; }
      else if (snake.x >= canvas.width) { snake.x = 0; }
      if (snake.y < 0) { snake.y = canvas.height - grid; }
      else if (snake.y >= canvas.height) { snake.y = 0; }

      snake.cells.unshift({x: snake.x, y: snake.y});
      if (snake.cells.length > snake.maxCells) { snake.cells.pop(); }

      context.fillStyle = 'red';
      context.fillRect(apple.x, apple.y, grid-1, grid-1);

      context.fillStyle = 'green';
      snake.cells.forEach(function(cell, index) {
        context.fillRect(cell.x, cell.y, grid-1, grid-1);
        // Comer manzana
        if (cell.x === apple.x && cell.y === apple.y) {
          snake.maxCells++;
          score++;
          apple.x = getRandomInt(0, 25) * grid;
          apple.y = getRandomInt(0, 25) * grid;
        }
        // Chocar contra sí misma
        for (var i = index + 1; i < snake.cells.length; i++) {
          if (cell.x === snake.cells[i].x && cell.y === snake.cells[i].y) {
            alert("¡Juego terminado! Lograste: " + score + " puntos. ¡Regístralo abajo!");
            snake.x = 160; snake.y = 160; snake.cells = []; snake.maxCells = 4; snake.dx = grid; snake.dy = 0; score = 0;
          }
        }
      });
    }
    // Controles de teclado
    document.addEventListener('keydown', function(e) {
      if (e.which === 37 && snake.dx === 0) { snake.dx = -grid; snake.dy = 0; }
      else if (e.which === 38 && snake.dy === 0) { snake.dy = -grid; snake.dx = 0; }
      else if (e.which === 39 && snake.dx === 0) { snake.dx = grid; snake.dy = 0; }
      else if (e.which === 40 && snake.dy === 0) { snake.dy = grid; snake.dx = 0; }
    });
    requestAnimationFrame(loop);
    </script>
    </body>
    </html>
    """
    components.html(snake_html, height=420)

    st.divider()
    
    st.subheader("💾 Guardar Puntuación")
    with st.form("score_form"):
        jugador = st.text_input("Nombre del jugador")
        puntuacion = st.number_input("Puntuación obtenida", min_value=0, step=1)
        submitted = st.form_submit_button("Guardar en MongoDB")

        if submitted:
            if jugador.strip():
                # Inserción de documento en MongoDB
                scores_collection.insert_one({
                    "jugador": jugador, 
                    "puntuacion": puntuacion
                })
                st.success(f"¡Puntuación de {puntuacion} guardada con éxito para {jugador}!")
            else:
                st.error("Por favor, ingresa un nombre.")

with tab2:
    st.header("🏆 Top Puntuaciones Históricas")
    
    if st.button("Actualizar tabla"):
        st.rerun()

    # Consulta a MongoDB: Traer todos los registros, ordenados de mayor a menor, límite 15
    cursor = scores_collection.find({}, {"_id": 0}).sort("puntuacion", -1).limit(15)
    scores_list = list(cursor)

    if scores_list:
        df = pd.DataFrame(scores_list)
        df.index = df.index + 1 # Para que el índice del ranking empiece en 1
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no hay puntuaciones guardadas en la base de datos.")