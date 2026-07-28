import mlflow

def run_test():
    print("Iniciando prueba de MLflow...")
    
    # Configurar el nombre del experimento
    mlflow.set_experiment("prueba_infraestructura_mlflow")

    # Iniciar un run de prueba
    with mlflow.start_run():
        # Registrar un parámetro y una métrica simulada
        mlflow.log_param("tipo_prueba", "infraestructura_basica")
        mlflow.log_metric("precision_simulada", 0.95)
        
        print("✅ Run completado. Parámetros y métricas registrados en MLflow correctamente.")

if __name__ == "__main__":
    run_test()