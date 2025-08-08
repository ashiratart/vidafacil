#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sql.h>
#include <sqlext.h>

int main() {
    SQLHENV hEnv = NULL;
    SQLHDBC hDbc = NULL;
    SQLHSTMT hStmt = NULL;
    SQLRETURN ret;

    // Dados de conexão
    const char *SERVER = "localhost";
    const char *DATABASE = "abc";
    const char *UID = "SeuUsuario";
    const char *PWD = "SuaSenha";

    // Montar connection string
    SQLCHAR connStr[512];
    snprintf((char *)connStr, sizeof(connStr),
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=%s;"
        "DATABASE=%s;"
        "UID=%s;"
        "PWD=%s;",
        SERVER, DATABASE, UID, PWD
    );

    // Alocar ambiente
    ret = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &hEnv);
    if (ret != SQL_SUCCESS && ret != SQL_SUCCESS_WITH_INFO) {
        fprintf(stderr, "Erro ao alocar ambiente.\n");
        return 1;
    }

    // Versão ODBC
    SQLSetEnvAttr(hEnv, SQL_ATTR_ODBC_VERSION, (void *)SQL_OV_ODBC3, 0);

    // Alocar conexão
    ret = SQLAllocHandle(SQL_HANDLE_DBC, hEnv, &hDbc);
    if (ret != SQL_SUCCESS && ret != SQL_SUCCESS_WITH_INFO) {
        fprintf(stderr, "Erro ao alocar conexão.\n");
        SQLFreeHandle(SQL_HANDLE_ENV, hEnv);
        return 1;
    }

    // Conectar
    ret = SQLDriverConnect(hDbc, NULL, connStr, SQL_NTS, NULL, 0, NULL, SQL_DRIVER_COMPLETE);
    if (!(ret == SQL_SUCCESS || ret == SQL_SUCCESS_WITH_INFO)) {
        fprintf(stderr, "Erro ao conectar ao banco.\n");
        SQLFreeHandle(SQL_HANDLE_DBC, hDbc);
        SQLFreeHandle(SQL_HANDLE_ENV, hEnv);
        return 1;
    }

    // Alocar handle de comando
    ret = SQLAllocHandle(SQL_HANDLE_STMT, hDbc, &hStmt);
    if (ret != SQL_SUCCESS && ret != SQL_SUCCESS_WITH_INFO) {
        fprintf(stderr, "Erro ao alocar handle de comando.\n");
        goto cleanup;
    }

    // Query para listar tabelas
    const char *sql = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;";
    ret = SQLExecDirect(hStmt, (SQLCHAR *)sql, SQL_NTS);
    if (!(ret == SQL_SUCCESS || ret == SQL_SUCCESS_WITH_INFO)) {
        fprintf(stderr, "Erro ao executar consulta.\n");
        goto cleanup;
    }

    // Abrir arquivo CSV
    FILE *fp = fopen("tabelas.csv", "w");
    if (!fp) {
        perror("Erro ao criar arquivo");
        goto cleanup;
    }

    fprintf(fp, "Tabela\n");  // Cabeçalho CSV

    // Recuperar nomes das tabelas
    SQLCHAR tableName[256];
    while ((ret = SQLFetch(hStmt)) != SQL_NO_DATA) {
        SQLGetData(hStmt, 1, SQL_C_CHAR, tableName, sizeof(tableName), NULL);
        fprintf(fp, "%s\n", tableName);
    }

    printf("✅ Tabelas salvas em 'tabelas.csv'.\n");
    fclose(fp);

cleanup:
    // Liberar recursos
    if (hStmt) SQLFreeHandle(SQL_HANDLE_STMT, hStmt);
    if (hDbc) {
        SQLDisconnect(hDbc);
        SQLFreeHandle(SQL_HANDLE_DBC, hDbc);
    }
    if (hEnv) SQLFreeHandle(SQL_HANDLE_ENV, hEnv);

    return 0;
}



/* #include <stdio.h>
#include <stdlib.h>
#include <mysql/mysql.h>

int main() {
    MYSQL *conn;
    const char *server = "localhost";
    const char *user = "seu_usuario";
    const char *password = "sua_senha";
    const char *database = "seu_banco";

    conn = mysql_init(NULL);

    if (conn == NULL) {
        fprintf(stderr, "mysql_init() falhou\n");
        exit(EXIT_FAILURE);
    }

    if (mysql_real_connect(conn, server, user, password, database, 0, NULL, 0) == NULL) {
        fprintf(stderr, "Falha na conexão: %s\n", mysql_error(conn));
        mysql_close(conn);
        exit(EXIT_FAILURE);
    }

    printf("Conexão com o banco de dados realizada com sucesso!\n");

    mysql_close(conn);
    return 0;
} */