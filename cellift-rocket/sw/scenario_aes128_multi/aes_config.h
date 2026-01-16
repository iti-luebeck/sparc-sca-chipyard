/**
 * AES-128 Configuration
 * 
 * Runtime configuration options for the AES benchmark
 */

#ifndef AES_CONFIG_H
#define AES_CONFIG_H

/* Number of times to repeat each encryption (for longer traces) */
#define REPEAT_COUNT 1

/* Number of NOPs to insert between encryptions (for trace splitting) */
#define NOP_DELIMITER_COUNT 100

/* Enable verification against expected ciphertexts */
#define VERIFY_RESULTS 1

/* Memory addresses for results storage */
#define RESULT_BASE_ADDR    0x80002000
#define STATUS_ADDR         0x80003000

/* Status codes written to STATUS_ADDR */
#define STATUS_RUNNING      0x01
#define STATUS_PASS         0xAA
#define STATUS_FAIL         0xFF

#endif /* AES_CONFIG_H */
