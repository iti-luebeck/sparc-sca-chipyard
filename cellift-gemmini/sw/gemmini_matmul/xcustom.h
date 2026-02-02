// Copyright 2018--2020 IBM
// RoCC custom instruction macros for Gemmini

#ifndef ROCC_SOFTWARE_SRC_XCUSTOM_H_
#define ROCC_SOFTWARE_SRC_XCUSTOM_H_

#define STR1(x) #x
#ifndef STR
#define STR(x) STR1(x)
#endif

#define CAT_(A, B) A##B
#define CAT(A, B) CAT_(A, B)

// C/C++ inline assembly macro for RoCC instructions that return data
#define ROCC_INSTRUCTION(x, rd, rs1, rs2, func7) \
  ROCC_INSTRUCTION_R_R_R(x, rd, rs1, rs2, func7)

#define ROCC_INSTRUCTION_R_R_R(x, rd, rs1, rs2, func7)                               \
  {                                                                                  \
    asm volatile(                                                                    \
        ".insn r " STR(CAT(CUSTOM_, x)) ", " STR(0x7) ", " STR(func7) ", %0, %1, %2" \
        : "=r"(rd)                                                                   \
        : "r"(rs1), "r"(rs2));                                                       \
  }

// C/C++ inline assembly macro for RoCC instructions that don't return data
#define ROCC_INSTRUCTION_0_R_R(x, rs1, rs2, func7)                                   \
  {                                                                                  \
    asm volatile(                                                                    \
        ".insn r " STR(CAT(CUSTOM_, x)) ", " STR(0x3) ", " STR(func7) ", x0, %0, %1" \
        :                                                                            \
        : "r"(rs1), "r"(rs2));                                                       \
  }

#endif  // ROCC_SOFTWARE_SRC_XCUSTOM_H_
