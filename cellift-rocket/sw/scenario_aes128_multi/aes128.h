/**
 * AES-128 Implementation Header
 */

#ifndef AES128_H
#define AES128_H

#include <stdint.h>

/**
 * Perform AES-128 encryption
 * 
 * @param plaintext  16-byte input plaintext
 * @param key        16-byte encryption key  
 * @param ciphertext 16-byte output buffer for ciphertext
 */
void aes128_encrypt(const uint8_t *plaintext, const uint8_t *key, uint8_t *ciphertext);

#endif /* AES128_H */
