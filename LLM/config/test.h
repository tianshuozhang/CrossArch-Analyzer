// This file is part of Eigen, a lightweight C++ template library
// for linear algebra.
//
// Copyright (C) 2008-2009 Gael Guennebaud <gael.guennebaud@inria.fr>
// Copyright (C) 2010 Konstantinos Margaritis <markos@freevec.org>
// Heavily based on Gael's SSE version.
//
// This Source Code Form is subject to the terms of the Mozilla
// Public License v. 2.0. If a copy of the MPL was not distributed
// with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

#ifndef EIGEN_PACKET_MATH_NEON_H
#define EIGEN_PACKET_MATH_NEON_H

// IWYU pragma: private
#include "../../InternalHeaderCheck.h"

namespace Eigen {

namespace internal {

#ifndef EIGEN_CACHEFRIENDLY_PRODUCT_THRESHOLD
#define EIGEN_CACHEFRIENDLY_PRODUCT_THRESHOLD 8
#endif

#ifndef EIGEN_HAS_SINGLE_INSTRUCTION_MADD
#define EIGEN_HAS_SINGLE_INSTRUCTION_MADD
#endif

#ifndef EIGEN_ARCH_DEFAULT_NUMBER_OF_REGISTERS
#if EIGEN_ARCH_ARM64
#define EIGEN_ARCH_DEFAULT_NUMBER_OF_REGISTERS 32
#else
#define EIGEN_ARCH_DEFAULT_NUMBER_OF_REGISTERS 16
#endif
#endif

#if EIGEN_COMP_MSVC_STRICT

// In MSVC's arm_neon.h header file, all NEON vector types
// are aliases to the same underlying type __n128.
// We thus have to wrap them to make them different C++ types.
// (See also bug 1428)
typedef eigen_packet_wrapper<float32x2_t, 0> Packet2f;
typedef eigen_packet_wrapper<float32x4_t, 1> Packet4f;
typedef eigen_packet_wrapper<int32_t, 2> Packet4c;
typedef eigen_packet_wrapper<int8x8_t, 3> Packet8c;
typedef eigen_packet_wrapper<int8x16_t, 4> Packet16c;
typedef eigen_packet_wrapper<uint32_t, 5> Packet4uc;
typedef eigen_packet_wrapper<uint8x8_t, 6> Packet8uc;
typedef eigen_packet_wrapper<uint8x16_t, 7> Packet16uc;
typedef eigen_packet_wrapper<int16x4_t, 8> Packet4s;
typedef eigen_packet_wrapper<int16x8_t, 9> Packet8s;
typedef eigen_packet_wrapper<uint16x4_t, 10> Packet4us;
typedef eigen_packet_wrapper<uint16x8_t, 11> Packet8us;
typedef eigen_packet_wrapper<int32x2_t, 12> Packet2i;
typedef eigen_packet_wrapper<int32x4_t, 13> Packet4i;
typedef eigen_packet_wrapper<uint32x2_t, 14> Packet2ui;
typedef eigen_packet_wrapper<uint32x4_t, 15> Packet4ui;
typedef eigen_packet_wrapper<int64x2_t, 16> Packet2l;
typedef eigen_packet_wrapper<uint64x2_t, 17> Packet2ul;

                                                                                
                               
                         
 

                                                              
                         
                        
 

#else

typedef float32x2_t Packet2f;
typedef float32x4_t Packet4f;
typedef eigen_packet_wrapper<int32_t, 2> Packet4c;
typedef int8x8_t Packet8c;
typedef int8x16_t Packet16c;
typedef eigen_packet_wrapper<uint32_t, 5> Packet4uc;
typedef uint8x8_t Packet8uc;
typedef uint8x16_t Packet16uc;
typedef int16x4_t Packet4s;
typedef int16x8_t Packet8s;
typedef uint16x4_t Packet4us;
typedef uint16x8_t Packet8us;
typedef int32x2_t Packet2i;
typedef int32x4_t Packet4i;
typedef uint32x2_t Packet2ui;
typedef uint32x4_t Packet4ui;
typedef int64x2_t Packet2l;
typedef uint64x2_t Packet2ul;

                                                                                                               
                                                                                       

#endif  // EIGEN_COMP_MSVC_STRICT

                                                                    
                                                      
                
                                                                                                                     
             
 

// functionally equivalent to _mm_shuffle_ps in SSE when interleave
// == false (i.e. shuffle<false>(m, n, mask) equals _mm_shuffle_ps(m, n, mask)),
// interleave m and n when interleave == true. Currently used in LU/arch/InverseSize4.h
// to enable a shared implementation for fast inversion of matrices of size 4.
template <bool interleave>
                                                                                       
                                                      
                                                      
                
                                                                                                                     
             
 

template <>
                                                                                             
                                                      
                                                      
                
                                                                                                                     
             
 

                                                                                    
                                                
 

                                                                                            
                                                          
 
                                                                                                               
                                                                    
 
                                                                                 
                                                                    
 
                                                                                 
                                                                    
 
                                                                                   
                                                                   
 
                                                                                   
                                                                   
 
#define vec4f_duplane(a, p) Packet4f(vdupq_lane_f32(vget_low_f32(a), p))

#define EIGEN_DECLARE_CONST_Packet4f(NAME, X) const Packet4f p4f_##NAME = pset1<Packet4f>(X)

#define EIGEN_DECLARE_CONST_Packet4f_FROM_INT(NAME, X) \
  const Packet4f p4f_##NAME = vreinterpretq_f32_u32(pset1<int32_t>(X))

#define EIGEN_DECLARE_CONST_Packet4i(NAME, X) const Packet4i p4i_##NAME = pset1<Packet4i>(X)

#if EIGEN_ARCH_ARM64 && EIGEN_COMP_GNUC
// __builtin_prefetch tends to do nothing on ARM64 compilers because the
// prefetch instructions there are too detailed for __builtin_prefetch to map
// meaningfully to them.
#define EIGEN_ARM_PREFETCH(ADDR) __asm__ __volatile__("prfm pldl1keep, [%[addr]]\n" ::[addr] "r"(ADDR) :);
#elif EIGEN_HAS_BUILTIN(__builtin_prefetch) || EIGEN_COMP_GNUC
#define EIGEN_ARM_PREFETCH(ADDR) __builtin_prefetch(ADDR);
#elif defined __pld
#define EIGEN_ARM_PREFETCH(ADDR) __pld(ADDR)
#elif EIGEN_ARCH_ARM
#define EIGEN_ARM_PREFETCH(ADDR) __asm__ __volatile__("pld [%[addr]]\n" ::[addr] "r"(ADDR) :);
#else
// by default no explicit prefetching
#define EIGEN_ARM_PREFETCH(ADDR)
#endif

template <>
struct packet_traits<float> : default_packet_traits {
  typedef Packet4f type;
  typedef Packet2f half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 4,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 1,
    HasAbs = 1,
    HasArg = 0,
    HasAbsDiff = 1,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
    HasDiv = 1,
    HasSin = EIGEN_FAST_MATH,
    HasCos = EIGEN_FAST_MATH,
    HasTan = EIGEN_FAST_MATH,
    HasACos = 1,
    HasASin = 1,
    HasATan = 1,
    HasATanh = 1,
    HasLog = 1,
    HasExp = 1,
    HasLog1p = 1,
    HasExpm1 = 1,
    HasPow = 1,
    HasSqrt = 1,
    HasRsqrt = 1,
    HasCbrt = 1,
    HasTanh = EIGEN_FAST_MATH,
    HasErf = EIGEN_FAST_MATH,
    HasErfc = EIGEN_FAST_MATH,
    HasBessel = 0,  // Issues with accuracy.
    HasNdtri = 0
  };
};

template <>
struct packet_traits<int8_t> : default_packet_traits {
  typedef Packet16c type;
  typedef Packet8c half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 16,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 1,
    HasAbs = 1,
    HasAbsDiff = 1,
    HasArg = 0,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
  };
};

template <>
struct packet_traits<uint8_t> : default_packet_traits {
  typedef Packet16uc type;
  typedef Packet8uc half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 16,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 0,
    HasAbs = 1,
    HasAbsDiff = 1,
    HasArg = 0,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,

    HasSqrt = 1
  };
};

template <>
struct packet_traits<int16_t> : default_packet_traits {
  typedef Packet8s type;
  typedef Packet4s half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 8,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 1,
    HasAbs = 1,
    HasAbsDiff = 1,
    HasArg = 0,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
  };
};

template <>
struct packet_traits<uint16_t> : default_packet_traits {
  typedef Packet8us type;
  typedef Packet4us half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 8,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 0,
    HasAbs = 1,
    HasAbsDiff = 1,
    HasArg = 0,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
    HasSqrt = 1
  };
};

template <>
struct packet_traits<int32_t> : default_packet_traits {
  typedef Packet4i type;
  typedef Packet2i half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 4,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 1,
    HasAbs = 1,
    HasArg = 0,
    HasAbsDiff = 1,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
  };
};

template <>
struct packet_traits<uint32_t> : default_packet_traits {
  typedef Packet4ui type;
  typedef Packet2ui half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 4,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 0,
    HasAbs = 1,
    HasArg = 0,
    HasAbsDiff = 1,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,

    HasSqrt = 1
  };
};

template <>
struct packet_traits<int64_t> : default_packet_traits {
  typedef Packet2l type;
  typedef Packet2l half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 2,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 1,
    HasAbs = 1,
    HasArg = 0,
    HasAbsDiff = 1,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
  };
};

template <>
struct packet_traits<uint64_t> : default_packet_traits {
  typedef Packet2ul type;
  typedef Packet2ul half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 2,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 0,
    HasAbs = 1,
    HasArg = 0,
    HasAbsDiff = 1,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
  };
};

template <typename Packet, typename Scalar>
struct neon_unpacket_default {
  using type = Scalar;
  using half = Packet;
  static constexpr int size = sizeof(Packet) / sizeof(Scalar);
  static constexpr int alignment = sizeof(Packet);
  static constexpr bool vectorizable = true;
  static constexpr bool masked_load_available = false;
  static constexpr bool masked_store_available = false;
};

template <>
struct unpacket_traits<Packet2f> : neon_unpacket_default<Packet2f, float> {
  using integer_packet = Packet2i;
};
template <>
struct unpacket_traits<Packet4f> : neon_unpacket_default<Packet4f, float> {
  using half = Packet2f;
  using integer_packet = Packet4i;
};
template <>
struct unpacket_traits<Packet4c> : neon_unpacket_default<Packet4c, int8_t> {};
template <>
struct unpacket_traits<Packet8c> : neon_unpacket_default<Packet8c, int8_t> {
  using half = Packet4c;
};
template <>
struct unpacket_traits<Packet16c> : neon_unpacket_default<Packet16c, int8_t> {
  using half = Packet8c;
};
template <>
struct unpacket_traits<Packet4uc> : neon_unpacket_default<Packet4uc, uint8_t> {};
template <>
struct unpacket_traits<Packet8uc> : neon_unpacket_default<Packet8uc, uint8_t> {
  using half = Packet4uc;
};
template <>
struct unpacket_traits<Packet16uc> : neon_unpacket_default<Packet16uc, uint8_t> {
  using half = Packet8uc;
};
template <>
struct unpacket_traits<Packet4s> : neon_unpacket_default<Packet4s, int16_t> {};
template <>
struct unpacket_traits<Packet8s> : neon_unpacket_default<Packet8s, int16_t> {
  using half = Packet4s;
};
template <>
struct unpacket_traits<Packet4us> : neon_unpacket_default<Packet4us, uint16_t> {};
template <>
struct unpacket_traits<Packet8us> : neon_unpacket_default<Packet8us, uint16_t> {
  using half = Packet4us;
};
template <>
struct unpacket_traits<Packet2i> : neon_unpacket_default<Packet2i, int32_t> {};
template <>
struct unpacket_traits<Packet4i> : neon_unpacket_default<Packet4i, int32_t> {
  using half = Packet2i;
};
template <>
struct unpacket_traits<Packet2ui> : neon_unpacket_default<Packet2ui, uint32_t> {};
template <>
struct unpacket_traits<Packet4ui> : neon_unpacket_default<Packet4ui, uint32_t> {
  using half = Packet2ui;
};
template <>
struct unpacket_traits<Packet2l> : neon_unpacket_default<Packet2l, int64_t> {};
template <>
struct unpacket_traits<Packet2ul> : neon_unpacket_default<Packet2ul, uint64_t> {};

template <>
                                                           
                          
 

template <>
                                                           
                           
 

template <>
                                                                 
                          
 
template <>
                                                                 
                           
 
template <>
                                                                  
                                                                
 
template <>
                                                                  
                         
 
template <>
                                                                    
                          
 
template <>
                                                                     
                                                                
 
template <>
                                                                     
                         
 
template <>
                                                                       
                          
 
template <>
                                                                   
                          
 
template <>
                                                                   
                           
 
template <>
                                                                      
                          
 
template <>
                                                                      
                           
 
template <>
                                                                   
                          
 
template <>
                                                                   
                           
 
template <>
                                                                      
                          
 
template <>
                                                                      
                           
 
template <>
                                                                   
                           
 
template <>
                                                                      
                           
 

template <>
                                                                     
                                                
 
template <>
                                                                     
                                                  
 

template <>
                                                              
                                 
                                                   
 
template <>
                                                              
                                             
                                                     
 
template <>
                                                               
                                                                                                                   
 
template <>
                                                               
                                              
                                                 
 
template <>
                                                                 
                                                                            
                                                    
 
template <>
                                                                  
                                                                                                                   
 
template <>
                                                                  
                                               
                                                  
 
template <>
                                                                    
                                                                             
                                                     
 
template <>
                                                                
                                   
                                                   
 
template <>
                                                                   
                                    
                                                    
 
template <>
                                                                
                                               
                                                     
 
template <>
                                                                   
                                                
                                                      
 
template <>
                                                                
                             
                                                   
 
template <>
                                                                
                                   
                                                     
 
template <>
                                                                   
                              
                                                    
 
template <>
                                                                   
                                    
                                                      
 
template <>
                                                                
                             
                                                     
 
template <>
                                                                   
                              
                                                      
 

template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                   
                       
                                                                                                               
 
template <>
                                                                                   
                       
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                       
                                                                                                               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                         
 

template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                   
                       
                                                                                                               
 
template <>
                                                                                   
                       
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                       
                                                                                                               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                         
 

template <>
EIGEN_STRONG_INLINE Packet2f pxor<Packet2f>(const Packet2f& a, const Packet2f& b);
template <>
                                                                                      
                                                                            
                                
 
template <>
EIGEN_STRONG_INLINE Packet4f pxor<Packet4f>(const Packet4f& a, const Packet4f& b);
template <>
                                                                                      
                                                                                                                        
                                
 

template <>
                                                         
                     
 
template <>
                                                         
                      
 
template <>
                                                         
                                                                                            
 
template <>
                                                         
                    
 
template <>
                                                           
                     
 
template <>
                                                         
                     
 
template <>
                                                         
                      
 
template <>
                                                         
                     
 
template <>
                                                         
                      
 
template <>
                                                         
                    
                      
     
                                                                                            
      
 

template <>
                                                       
           
 
template <>
                                                       
           
 
template <>
                                                       
           
 
template <>
                                                       
           
 
template <>
                                                         
           
 
template <>
                                                         
           
 
template <>
                                                         
           
 
template <>
                                                           
           
 
template <>
                                                       
           
 
template <>
                                                       
           
 
template <>
                                                         
           
 
template <>
                                                         
           
 
template <>
                                                       
           
 
template <>
                                                       
           
 
template <>
                                                         
           
 
template <>
                                                         
           
 
template <>
                                                       
           
 
template <>
                                                         
           
 

template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                   
                       
                                                                                                               
 
template <>
                                                                                   
                       
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                       
                                                                                                               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                                                                              
                                                                               
 
template <>
                                                                                       
                                                                              
                                                                               
 

template <>
                                                                                           
                                                                             
                            
 
template <>
                                                                                           
                                                                             
                            
 
template <>
                                                                                               
                                                                             
                             
 
template <>
                                                                                               
                                                                             
                             
 
template <>
                                                                                               
                                                                             
                             
 
template <>
                                                                                                   
                                                                             
                              
 
template <>
                                                                                           
                                                                             
                            
 
template <>
                                                                                           
                                                                             
                            
 
template <>
                                                                                               
                                                                             
                             
 
template <>
                                                                                               
                                                                             
                             
 
template <>
                                                                                           
                                                                             
                            
 
template <>
                                                                                           
                                                                             
                            
 
template <>
                                                                                               
                                                                             
                             
 
template <>
                                                                                               
                                                                             
                             
 
template <>
                                                                                           
                                                                             
                              
 
template <>
                                                                                               
                                                                             
                                
 

#ifdef EIGEN_VECTORIZE_FMA
template <>
                                                                                             
                            
 
template <>
                                                                                             
                           
 
template <>
                                                                                              
                            
 
template <>
                                                                                              
                           
 
#else
template <>
                                                                                             
                            
 
template <>
                                                                                             
                           
 
template <>
                                                                                              
                            
 
template <>
                                                                                              
                           
 
#endif
template <>
                                                                                             
                                  
 
template <>
                                                                                             
                                  
 
template <>
                                                                                              
                                 
 
template <>
                                                                                              
                                 
 

// No FMA instruction for int, so use MLA unconditionally.
template <>
                                                                                             
                       
                                                                                                         
                                                                       
         
 
template <>
                                                                                             
                          
 
template <>
                                                                                                 
                           
 
template <>
                                                                                                 
                       
                                                                                                         
                                                                       
         
 
template <>
                                                                                                 
                          
 
template <>
                                                                                                     
                           
 
template <>
                                                                                             
                           
 
template <>
                                                                                             
                            
 
template <>
                                                                                                 
                           
 
template <>
                                                                                                 
                            
 
template <>
                                                                                             
                           
 
template <>
                                                                                             
                            
 
template <>
                                                                                                 
                           
 
template <>
                                                                                                 
                            
 

template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                       
                       
                                                                                                               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                           
                       
                                                                                                               
 
template <>
                                                                                           
                       
 
template <>
                                                                                               
                        
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                           
                        
 
template <>
                                                                                           
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                           
                        
 
template <>
                                                                                           
                         
 

template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 

#ifdef __ARM_FEATURE_NUMERIC_MAXMIN
// numeric max and min are only available if ARM_FEATURE_NUMERIC_MAXMIN is defined (which can only be the case for Armv8
// systems).
template <>
                                                                                                     
                           
 
template <>
                                                                                                     
                          
 
#endif

template <>
                                                                                                 
                              
 

template <>
                                                                                                 
                              
 

template <>
                                                                                   
                       
                                                                                                               
 
template <>
                                                                                   
                       
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                       
                                                                                                               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                                                                                         
                                                                                          
 
template <>
                                                                                       
                                                                                         
                                                                                          
 

template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 

#ifdef __ARM_FEATURE_NUMERIC_MAXMIN
// numeric max and min are only available if ARM_FEATURE_NUMERIC_MAXMIN is defined (which can only be the case for Armv8
// systems).
template <>
                                                                                                     
                           
 
template <>
                                                                                                     
                          
 
#endif

template <>
                                                                                                 
                              
 

template <>
                                                                                                 
                              
 

template <>
                                                                                   
                       
                                                                                                               
 
template <>
                                                                                   
                       
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                       
                                                                                                               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                                                                                         
                                                                                          
 
template <>
                                                                                       
                                                                                         
                                                                                          
 

template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                      
                       
                                                                                                               
 
template <>
                                                                                      
                                           
 
template <>
                                                                                          
                                             
 
template <>
                                                                                          
                       
                                                                                                               
 
template <>
                                                                                          
                       
 
template <>
                                                                                              
                        
 
template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                    
                                                
     
                                                                                                         
                                                                                                          
      
 
template <>
                                                                                          
                    
                         
     
                                                                                                          
                                                                                                           
      
 

template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                      
                       
                                                                                                               
 
template <>
                                                                                      
                                           
 
template <>
                                                                                          
                                             
 
template <>
                                                                                          
                       
                                                                                                               
 
template <>
                                                                                          
                       
 
template <>
                                                                                              
                        
 
template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                    
                                                
     
                                                                                                        
                                                                                                         
      
 
template <>
                                                                                          
                    
                         
     
                                                                                                         
                                                                                                          
      
 

template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                      
                       
                                                                                                               
 
template <>
                                                                                      
                                           
 
template <>
                                                                                          
                                             
 
template <>
                                                                                          
                       
                                                                                                               
 
template <>
                                                                                          
                       
 
template <>
                                                                                              
                        
 
template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                                              
 
template <>
                                                                                      
                                                
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                    
                                                
     
                                                                                                         
                                                                                                          
      
 
template <>
                                                                                          
                    
                         
     
                                                                                                          
                                                                                                           
      
 

template <>
                                                                                             
                                                        
 
template <>
                                                                                             
                                                           
 

// Logical Operations are not supported for float, so we have to reinterpret casts using NEON intrinsics
template <>
                                                                                   
                                                                                          
 
template <>
                                                                                   
                                                                                              
 
template <>
                                                                                   
               
 
template <>
                                                                                   
                       
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                         
 

template <>
                                                                                  
                                                                                          
 
template <>
                                                                                  
                                                                                              
 
template <>
                                                                                  
               
 
template <>
                                                                                  
                       
 
template <>
                                                                                      
                        
 
template <>
                                                                                      
               
 
template <>
                                                                                      
                       
 
template <>
                                                                                          
                        
 
template <>
                                                                                  
                        
 
template <>
                                                                                  
                         
 
template <>
                                                                                      
                        
 
template <>
                                                                                      
                         
 
template <>
                                                                                  
                        
 
template <>
                                                                                  
                         
 
template <>
                                                                                      
                        
 
template <>
                                                                                      
                         
 
template <>
                                                                                  
                         
 
template <>
                                                                                      
                         
 

template <>
                                                                                   
                                                                                          
 
template <>
                                                                                   
                                                                                              
 
template <>
                                                                                   
               
 
template <>
                                                                                   
                       
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
               
 
template <>
                                                                                       
                       
 
template <>
                                                                                           
                        
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                        
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                        
 
template <>
                                                                                       
                         
 
template <>
                                                                                   
                         
 
template <>
                                                                                       
                         
 

template <>
                                                                                      
                                                                                          
 
template <>
                                                                                      
                                                                                              
 
template <>
                                                                                      
                
 
template <>
                                                                                      
                       
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                
 
template <>
                                                                                          
                       
 
template <>
                                                                                              
                        
 
template <>
                                                                                      
                        
 
template <>
                                                                                      
                         
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                        
 
template <>
                                                                                      
                         
 
template <>
                                                                                          
                        
 
template <>
                                                                                          
                         
 
template <>
                                                                                      
                         
 
template <>
                                                                                          
                         
 

template <int N>
                                                                   
                                                                                                 
 
template <int N>
                                                                  
                         
 
template <int N>
                                                                    
                          
 
template <int N>
                                                                     
                                                                                                 
 
template <int N>
                                                                    
                         
 
template <int N>
                                                                      
                          
 
template <int N>
                                                                  
                          
 
template <int N>
                                                                  
                           
 
template <int N>
                                                                    
                          
 
template <int N>
                                                                    
                           
 
template <int N>
                                                                  
                          
 
template <int N>
                                                                  
                           
 
template <int N>
                                                                    
                          
 
template <int N>
                                                                    
                           
 
template <int N>
                                                                  
                           
 
template <int N>
                                                                    
                           
 

template <int N>
                                                                
                                                                                                 
 
template <int N>
                                                               
                                                                 
 
template <int N>
                                                                 
                                                                    
 
template <int N>
                                                                  
                                                                                                 
 
template <int N>
                                                                 
                         
 
template <int N>
                                                                   
                          
 
template <int N>
                                                               
                                                                      
 
template <int N>
                                                               
                                                                         
 
template <int N>
                                                                 
                          
 
template <int N>
                                                                 
                           
 
template <int N>
                                                               
                                                                      
 
template <int N>
                                                               
                                                                         
 
template <int N>
                                                                 
                          
 
template <int N>
                                                                 
                           
 
template <int N>
                                                               
                                                                         
 
template <int N>
                                                                 
                           
 

template <int N>
                                                               
                                                                                                 
 
template <int N>
                                                              
                         
 
template <int N>
                                                                
                          
 
template <int N>
                                                                 
                                                                                                 
 
template <int N>
                                                                
                         
 
template <int N>
                                                                  
                          
 
template <int N>
                                                              
                          
 
template <int N>
                                                              
                           
 
template <int N>
                                                                
                          
 
template <int N>
                                                                
                           
 
template <int N>
                                                              
                          
 
template <int N>
                                                              
                           
 
template <int N>
                                                                
                          
 
template <int N>
                                                                
                           
 
template <int N>
                                                              
                           
 
template <int N>
                                                                
                           
 

template <>
                                                                 
                                                                                                       
 
template <>
                                                                 
                                                                                                        
 
template <>
                                                                  
               
                                       
             
 
template <>
                                                                  
                                                                                                      
 
template <>
                                                                    
                                                                                                        
 
template <>
                                                                     
                
                                        
             
 
template <>
                                                                     
                                                                                                       
 
template <>
                                                                       
                                                                                                         
 
template <>
                                                                   
                                                                                                       
 
template <>
                                                                   
                                                                                                        
 
template <>
                                                                      
                                                                                                        
 
template <>
                                                                      
                                                                                                         
 
template <>
                                                                   
                                                                                                       
 
template <>
                                                                   
                                                                                                        
 
template <>
                                                                      
                                                                                                        
 
template <>
                                                                      
                                                                                                         
 
template <>
                                                                   
                                                                                                        
 
template <>
                                                                      
                                                                                                         
 

template <>
                                                                  
                                                   
 
template <>
                                                                  
                                                    
 
template <>
                                                                   
               
                                       
             
 
template <>
                                                                   
                                                  
 
template <>
                                                                     
                                                   
 
template <>
                                                                      
                
                                        
             
 
template <>
                                                                      
                                                  
 
template <>
                                                                        
                                                   
 
template <>
                                                                    
                                                   
 
template <>
                                                                    
                                                    
 
template <>
                                                                       
                                                   
 
template <>
                                                                       
                                                    
 
template <>
                                                                    
                                                   
 
template <>
                                                                    
                                                    
 
template <>
                                                                       
                                                   
 
template <>
                                                                       
                                                    
 
template <>
                                                                    
                                                    
 
template <>
                                                                       
                                                    
 

template <>
                                                                    
                            
 
template <>
                                                                    
                                                                  
 
template <>
                                                                     
                                                                            
                                                                     
 
template <>
                                                                     
                                   
                              
 
template <>
                                                                       
                                   
                                     
                                         
 
template <>
                                                                        
                                                                              
                                                                     
 
template <>
                                                                        
                                    
                              
 
template <>
                                                                          
                                    
                                      
                                         
 
template <>
                                                                      
                              
                                                                                                               
 
template <>
                                                                      
                                     
                                       
                                          
 
template <>
                                                                         
                              
                                                                                                               
 
template <>
                                                                         
                                      
                                        
                                          
 
template <>
                                                                      
                            
 
template <>
                                                                      
                                                                  
 
template <>
                                                                         
                            
 
template <>
                                                                         
                                                                  
 
template <>
                                                                      
                             
 
template <>
                                                                         
                             
 

template <>
                                                                     
                             
 
template <>
                                                                      
                                                                  
 
template <>
                                                                      
                             
                                                                                                           
 
template <>
                                                                        
                                         
                                                                                                           
                                         
                                                                                                               
                           
 
template <>
                                                                         
                                                                  
 
template <>
                                                                         
                             
                                                                                                           
 
template <>
                                                                           
                                          
                                                                                                           
                                          
                                                                                                               
                           
 
template <>
                                                                       
                                                                  
 
template <>
                                                                          
                                                                  
 
template <>
                                                                       
                             
 
template <>
                                                                          
                             
 

template <>
                                                                         
                                                                                                     
 
template <>
                                                                         
                                                                                                      
 
template <>
                                                                           
                                  
 
template <>
                                                                           
                                                                                                    
 
template <>
                                                                            
                                                                                                      
 
template <>
                                                                              
                                  
 
template <>
                                                                              
                                                                                                     
 
template <>
                                                                               
                                                                                                       
 
template <>
                                                                             
                                                                                                     
 
template <>
                                                                             
                                                                                                      
 
template <>
                                                                                
                                                                                                      
 
template <>
                                                                                
                                                                                                       
 
template <>
                                                                             
                                                                                                     
 
template <>
                                                                             
                                                                                                      
 
template <>
                                                                                
                                                                                                      
 
template <>
                                                                                
                                                                                                       
 
template <>
                                                                             
                                                                                                      
 
template <>
                                                                                
                                                                                                       
 

template <>
                                                                          
                                                 
 
template <>
                                                                          
                                                  
 
template <>
                                                                            
                                  
 
template <>
                                                                            
                                                
 
template <>
                                                                             
                                                 
 
template <>
                                                                               
                                  
 
template <>
                                                                               
                                                
 
template <>
                                                                                
                                                 
 
template <>
                                                                              
                                                 
 
template <>
                                                                              
                                                  
 
template <>
                                                                                 
                                                 
 
template <>
                                                                                 
                                                  
 
template <>
                                                                              
                                                 
 
template <>
                                                                              
                                                  
 
template <>
                                                                                 
                                                 
 
template <>
                                                                                 
                                                  
 
template <>
                                                                              
                                                  
 
template <>
                                                                                 
                                                  
 

template <>
                                                                                                          
                                    
                                                 
             
 
template <>
                                                                                                          
                                     
                                                  
                                                  
                                                  
             
 
template <>
                                                                                                            
               
                                                                                         
             
 
template <>
                                                                                                            
                                   
                                                
                                                
                                                
                                                
                                                
                                                
                                                
             
 
template <>
                                                                                                              
                                     
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                   
                                                   
                                                   
                                                   
                                                   
                                                   
             
 
template <>
                                                                                                                
                
                                                                                          
             
 
template <>
                                                                                                                
                                    
                                                
                                                
                                                
                                                
                                                
                                                
                                                
             
 
template <>
                                                                                                                  
                                      
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                 
                                                   
                                                   
                                                   
                                                   
                                                   
                                                   
             
 
template <>
                                                                                                              
                                    
                                                 
                                                 
                                                 
             
 
template <>
                                                                                                              
                                     
                                                  
                                                  
                                                  
                                                  
                                                  
                                                  
                                                  
             
 
template <>
                                                                                                                  
                                     
                                                 
                                                 
                                                 
             
 
template <>
                                                                                                                  
                                      
                                                  
                                                  
                                                  
                                                  
                                                  
                                                  
                                                  
             
 
template <>
                                                                                                              
                                    
                                                 
             
 
template <>
                                                                                                              
                                     
                                                  
                                                  
                                                  
             
 
template <>
                                                                                                                  
                                     
                                                 
             
 
template <>
                                                                                                                  
                                      
                                                  
                                                  
                                                  
             
 
template <>
                                                                                                              
                                     
                                                  
             
 
template <>
                                                                                                                  
                                      
                                                  
             
 

template <>
                                                                                                                     
                                          
                                          
 
template <>
                                                                                                                     
                                           
                                           
                                           
                                           
 
template <>
                                                                                                                       
                                                                                              
 
template <>
                                                                                                                       
                                         
                                         
                                         
                                         
                                         
                                         
                                         
                                         
 
template <>
                                                                                                         
                                                                                      
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                            
                                            
                                            
                                            
                                            
                                            
 
template <>
                                                                                                           
                                                                                       
                                                                                               
 
template <>
                                                                                                           
                                                                                       
                                         
                                         
                                         
                                         
                                         
                                         
                                         
                                         
 
template <>
                                                                                                             
                                                                                        
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                          
                                            
                                            
                                            
                                            
                                            
                                            
 
template <>
                                                                                                         
                                                                                      
                                          
                                          
                                          
                                          
 
template <>
                                                                                                         
                                                                                      
                                           
                                           
                                           
                                           
                                           
                                           
                                           
                                           
 
template <>
                                                                                                             
                                                                                        
                                          
                                          
                                          
                                          
 
template <>
                                                                                                             
                                                                                        
                                           
                                           
                                           
                                           
                                           
                                           
                                           
                                           
 
template <>
                                                                                                         
                                                                                      
                                          
                                          
 
template <>
                                                                                                         
                                                                                      
                                           
                                           
                                           
                                           
 
template <>
                                                                                                             
                                                                                        
                                          
                                          
 
template <>
                                                                                                             
                                                                                        
                                           
                                           
                                           
                                           
 
template <>
                                                                                                         
                                                                                      
                                           
                                           
 
template <>
                                                                                                             
                                                                                        
                                           
                                           
 

template <>
                                                             
                           
 
template <>
                                                               
                           
 
template <>
                                                                 
                           
 
template <>
                                                                 
                           
 
template <>
                                                                   
                           
 
template <>
                                                                 
                           
 
template <>
                                                                   
                           
 
template <>
                                                                 
                           
 
template <>
                                                                   
                           
 

template <>
                                                               
                             
 
template <>
                                                               
                              
 
template <>
                                                                
                                       
 
template <>
                                                                
                            
 
template <>
                                                                  
                             
 
template <>
                                                                   
                                        
 
template <>
                                                                   
                            
 
template <>
                                                                     
                             
 
template <>
                                                                 
                             
 
template <>
                                                                 
                              
 
template <>
                                                                    
                             
 
template <>
                                                                    
                              
 
template <>
                                                                 
                             
 
template <>
                                                                 
                              
 
template <>
                                                                    
                             
 
template <>
                                                                    
                              
 
template <>
                                                                 
                              
 
template <>
                                                                    
                              
 

template <>
                                                          
                       
 
template <>
                                                          
                                           
                                                                 
 
template <>
                                                          
                                                                                              
 
template <>
                                                          
                      
 
template <>
                                                            
                                        
                                                              
 
template <>
                                                            
                                                                                              
 
template <>
                                                            
                      
 
template <>
                                                              
                                         
                                                              
 
template <>
                                                          
                       
 
template <>
                                                          
                                         
                                                                 
 
template <>
                                                            
                       
 
template <>
                                                            
                                          
                                                                 
 
template <>
                                                          
                       
 
template <>
                                                          
                                         
                                                                 
 
template <>
                                                            
                       
 
template <>
                                                            
                                          
                                                                 
 
template <>
                                                          
                                                         
 
template <>
                                                            
                                                         
 

template <>
                                                      
                     
 
template <>
                                                      
                      
 
template <>
                                                                
                                                                                            
 
template <>
                                                      
                    
 
template <>
                                                        
                     
 
template <>
                                                        
           
 
template <>
                                                        
           
 
template <>
                                                          
           
 
template <>
                                                      
                     
 
template <>
                                                      
                      
 
template <>
                                                        
           
 
template <>
                                                        
           
 
template <>
                                                      
                     
 
template <>
                                                      
                      
 
template <>
                                                        
           
 
template <>
                                                        
           
 
template <>
                                                      
                    
                      
     
                                                                                                                  
      
 
template <>
                                                        
           
 

template <>
                                                          
                                                                       
 
template <>
                                                          
                                                                          
 

template <>
                                                                                      
                                     
 
template <>
                                                                                      
                                     
 

template <>
                                                                                            
                                     
 
template <>
                                                                                            
                                     
 

#if EIGEN_ARCH_ARM64
template <>
                                                               
                      
 
template <>
                                                               
                       
 
#else
template <>
                                                               
                                           
 
template <>
                                                               
                                                                      
                                               
 
#endif
template <>
                                                                
                                                            
                                        
                           
                              
 
#if EIGEN_ARCH_ARM64
template <>
                                                                
                     
 
template <>
                                                                  
                      
 
#else
template <>
                                                                
                                
                           
                           
                              
 
template <>
                                                                  
                                                          
                           
                           
                           
                              
 
#endif
template <>
                                                                   
                                                             
                                         
                           
                              
 
#if EIGEN_ARCH_ARM64
template <>
                                                                   
                     
 
template <>
                                                                     
                      
 
template <>
                                                                 
                      
 
template <>
                                                                 
                       
 
template <>
                                                                    
                      
 
template <>
                                                                    
                       
 
template <>
                                                                 
                      
 
template <>
                                                                 
                       
 
template <>
                                                                    
                      
 
template <>
                                                                    
                       
 
template <>
                                                                 
                       
 
template <>
                                                                    
                       
 
#else
template <>
                                                                   
                                 
                           
                           
                              
 
template <>
                                                                     
                                                           
                           
                           
                           
                              
 
template <>
                                                                 
                                        
                                               
 
template <>
                                                                 
                                                              
                            
                            
                               
 
template <>
                                                                    
                                         
                                               
 
template <>
                                                                    
                                                               
                            
                            
                               
 
template <>
                                                                 
                                           
 
template <>
                                                                 
                                                                    
                                               
 
template <>
                                                                    
                                           
 
template <>
                                                                    
                                                                     
                                               
 
template <>
                                                                 
                                                     
 
template <>
                                                                    
                                                     
 
#endif

template <>
                                                                               
                                                                                                                    
 
template <>
                                                                                
                                                  
 
template <>
                                                                                 
                                                                                                                    
 
template <>
                                                                                  
                                                  
 
template <>
                                                                               
                                                     
 
template <>
                                                                                 
                                                     
 

// Other reduction functions:
// mul
template <>
                                                                   
                                                   
 
template <>
                                                                   
                                                                           
 
template <>
                                                                    
                                                     
                                        
                                                       
 
template <>
                                                                    
                                           
                                        
                                                       
 
template <>
                                                                      
                                                                        
 
template <>
                                                                       
                                                      
                                        
                                                       
 
template <>
                                                                       
                                            
                                        
                                                       
 
template <>
                                                                         
                                                                         
 
template <>
                                                                     
                                                    
                                                         
 
template <>
                                                                     
                 

                                                                
                                                     
                                                
                                          
                                       
                                                         
 
template <>
                                                                        
                                                     
                                                         
 
template <>
                                                                        
                  

                                                                
                                                     
                                                
                                          
                                       
                                                         
 
template <>
                                                                     
                                                   
 
template <>
                                                                     
                                                                           
 
template <>
                                                                        
                                                   
 
template <>
                                                                        
                                                                            
 
template <>
                                                                     
                                                     
 
template <>
                                                                        
                                                     
 

// min
#if EIGEN_ARCH_ARM64
template <>
                                                                   
                      
 
template <>
                                                                   
                       
 
#else
template <>
                                                                   
                                           
 
template <>
                                                                   
                                                                      
                                               
 
#endif
template <>
                                                                    
                                                            
                                        
                           
                              
 
#if EIGEN_ARCH_ARM64
template <>
                                                                    
                     
 
template <>
                                                                      
                      
 
#else
template <>
                                                                    
                                
                           
                           
                              
 
template <>
                                                                      
                                                          
                           
                           
                           
                              
 
#endif
template <>
                                                                       
                                                             
                                         
                           
                              
 
#if EIGEN_ARCH_ARM64
template <>
                                                                       
                     
 
template <>
                                                                         
                      
 
template <>
                                                                     
                      
 
template <>
                                                                     
                       
 
template <>
                                                                        
                      
 
template <>
                                                                        
                       
 
template <>
                                                                     
                      
 
template <>
                                                                     
                       
 
template <>
                                                                        
                      
 
template <>
                                                                        
                       
 
#else
template <>
                                                                       
                                 
                           
                           
                              
 
template <>
                                                                         
                                                           
                           
                           
                           
                              
 
template <>
                                                                     
                                        
                                               
 
template <>
                                                                     
                                                              
                            
                            
                               
 
template <>
                                                                        
                                         
                                               
 
template <>
                                                                        
                                                               
                            
                            
                               
 
template <>
                                                                     
                                           
 
template <>
                                                                     
                                                                    
                                               
 
template <>
                                                                        
                                           
 
template <>
                                                                        
                                                                     
                                               
 
#endif
template <>
                                                                     
                                                                
 
template <>
                                                                        
                                                                
 

// max
#if EIGEN_ARCH_ARM64
template <>
                                                                   
                      
 
template <>
                                                                   
                       
 
#else
template <>
                                                                   
                                           
 
template <>
                                                                   
                                                                      
                                               
 
#endif
template <>
                                                                    
                                                            
                                        
                           
                              
 
#if EIGEN_ARCH_ARM64
template <>
                                                                    
                     
 
template <>
                                                                      
                      
 
#else
template <>
                                                                    
                                
                           
                           
                              
 
template <>
                                                                      
                                                          
                           
                           
                           
                              
 
#endif
template <>
                                                                       
                                                             
                                         
                           
                              
 
#if EIGEN_ARCH_ARM64
template <>
                                                                       
                     
 
template <>
                                                                         
                      
 
template <>
                                                                     
                      
 
template <>
                                                                     
                       
 
template <>
                                                                        
                      
 
template <>
                                                                        
                       
 
template <>
                                                                     
                      
 
template <>
                                                                     
                       
 
template <>
                                                                        
                      
 
template <>
                                                                        
                       
 
#else
template <>
                                                                       
                                 
                           
                           
                              
 
template <>
                                                                         
                                                           
                           
                           
                           
                              
 
template <>
                                                                     
                                        
                                               
 
template <>
                                                                     
                                                              
                            
                            
                               
 
template <>
                                                                        
                                         
                                               
 
template <>
                                                                        
                                                               
                            
                            
                               
 
template <>
                                                                     
                                           
 
template <>
                                                                     
                                                                    
                                               
 
template <>
                                                                        
                                           
 
template <>
                                                                        
                                                                     
                                               
 
#endif
template <>
                                                                     
                                                                
 
template <>
                                                                        
                                                                
 

template <>
                                                        
                                                                                                             
                                               
 

// Helpers for ptranspose.
namespace detail {

template <typename Packet>
void zip_in_place(Packet& p1, Packet& p2);

template <>
                                                                             
                                             
                  
                  
 

template <>
                                                                             
                                              
                  
                  
 

template <>
                                                                             
                                         
                  
                  
 

template <>
                                                                                
                                           
                  
                  
 

template <>
                                                                                
                                          
                  
                  
 

template <>
                                                                                   
                                            
                  
                  
 

template <>
                                                                             
                                           
                  
                  
 

template <>
                                                                             
                                            
                  
                  
 

template <>
                                                                                
                                            
                  
                  
 

template <>
                                                                                
                                             
                  
                  
 

template <>
                                                                             
                                           
                  
                  
 

template <>
                                                                             
                                            
                  
                  
 

template <>
                                                                                
                                            
                  
                  
 

template <>
                                                                                
                                             
                  
                  
 

template <typename Packet>
                                                                          
                                                   
 

template <typename Packet>
                                                                          
                                                   
                                                   
                                                   
                                                   
 

template <typename Packet>
                                                                          
                                                   
                                                   
                                                   
                                                   

                                                   
                                                   
                                                   
                                                   

                                                   
                                                   
                                                   
                                                   
 

template <typename Packet>
                                                                           
                   
                               
                           
                     
                                 
                                   
                       
                                   
                                      
                                                                 
       
     
   
 

}  // namespace detail

                                                                                         
                                  
 
                                                                                         
                                  
 

                                                                                         
                                                                                                           
                                                                                                           

                                        
                                                                                                         

                                                                          
                                                                          
                                                                          
                                                                          
 
                                                                                         
                                  
 
                                                                                         
                                  
 
                                                                                           
                                  
 
                                                                                          
                                  
 
                                                                                          
                                  
 

                                                                                          
                                                                                                            
                                                                                                            

                                         
                                                                                                          

                                                                          
                                                                          
                                                                          
                                                                          
 
                                                                                          
                                  
 
                                                                                          
                                  
 
                                                                                            
                                  
 
                                                                                           
                                  
 
                                                                                           
                                  
 

                                                                                         
                                  
 
                                                                                         
                                  
 
                                                                                         
                                  
 

                                                                                          
                                  
 
                                                                                          
                                  
 
                                                                                          
                                  
 

                                                                                         
                                  
 
                                                                                         
                                  
 
                                                                                          
                                                           
 
                                                                                          
                                  
 

                                                                                         
                    
                                                                        
                                                                    
                          
     
                                                                                                 
                                                                                                  

                                                        
                                                        
      
 
                                                                                          
                    
                                                                         
                                                                    
                          
     
                                                                                                  
                                                                                                   

                                                        
                                                        
      
 

template <>
                                                                                                                    
                                                    
 
template <>
                                                                                                                    
                                                      
 
template <>
                                                                                                                    
                                                 
 
template <>
                                                                                                                        
                                                   
 
template <>
                                                                                                                        
                             
 
template <>
                                                                                                     
                                                                               
                              
 
template <>
                                                                                                                    
                                                    
 
template <>
                                                                                                                    
                                                      
 
template <>
                                                                                                                        
                              
 
template <>
                                                                                                                        
                               
 
template <>
                                                                                                                    
                                                    
 
template <>
                                                                                                                    
                                                      
 
template <>
                                                                                                                        
                              
 
template <>
                                                                                                                        
                               
 
template <>
                                                                                                                    
                                                      
 
template <>
                                                                                                                        
                               
 

// Use armv8 rounding intinsics if available.
#if EIGEN_ARCH_ARMV8
template <>
                                                                 
                      
 

template <>
                                                                 
                       
 

template <>
                                                                  
                      
 

template <>
                                                                  
                       
 

template <>
                                                                 
                      
 

template <>
                                                                 
                       
 

template <>
                                                                  
                      
 

template <>
                                                                  
                       
 

template <>
                                                                  
                     
 

template <>
                                                                  
                      
 
#endif

/**
 * Computes the integer square root
 * @remarks The calculation is performed using an algorithm which iterates through each binary digit of the result
 *   and tests whether setting that digit to 1 would cause the square of the value to be greater than the argument
 *   value. The algorithm is described in detail here: http://ww1.microchip.com/downloads/en/AppNotes/91040a.pdf .
 */
template <>
                                                         
                                                   
                               
                                 
                               
                                             
                                                              
                            
   
                                                    
 
/// @copydoc Eigen::internal::psqrt(const Packet4uc& a)
template <>
                                                         
                               
                                 
                               
                                             
                                                              
                            
   
             
 
/// @copydoc Eigen::internal::psqrt(const Packet4uc& a)
template <>
                                                           
                                 
                                   
                               
                                               
                                                                 
                             
   
             
 
/// @copydoc Eigen::internal::psqrt(const Packet4uc& a)
template <>
                                                         
                                 
                                    
                               
                                               
                                                                 
                             
   
             
 
/// @copydoc Eigen::internal::psqrt(const Packet4uc& a)
template <>
                                                         
                                  
                                     
                               
                                                
                                                                    
                              
   
             
 
/// @copydoc Eigen::internal::psqrt(const Packet4uc& a)
template <>
                                                         
                                 
                                      
                                
                                               
                                                                 
                             
   
             
 
/// @copydoc Eigen::internal::psqrt(const Packet4uc& a)
template <>
                                                         
                                  
                                       
                                
                                                
                                                                    
                              
   
             
 

                                                                     
                                         
                                            
                                       
                                                                         
                                                                         
                
 

                                                                     
                                         
                                            
                                      
                                                                      
                                                                      
                
 

template <typename Packet>
Packet prsqrt_float_common(const Packet& a) {
  const Packet cst_zero = pzero(a);
  const Packet cst_inf = pset1<Packet>(NumTraits<float>::infinity());
  Packet return_zero = pcmp_eq(a, cst_inf);
  Packet return_inf = pcmp_eq(a, cst_zero);
  Packet result = prsqrt_float_unsafe(a);
  result = pselect(return_inf, por(cst_inf, a), result);
  result = pandnot(result, return_zero);
  return result;
}

template <>
                                                        
                                
 

template <>
                                                        
                                
 

template <>
                                                                       
                                    
                                      
                                                     
                                                     
                
 

template <>
                                                                       
                                    
                                     
                                                   
                                                   
                
 

// Unfortunately vsqrt_f32 is only available for A64.
#if EIGEN_ARCH_ARM64
template <>
                                                       
                       
 

template <>
                                                       
                      
 

template <>
                                                                         
                         
 

template <>
                                                                         
                        
 
#else
template <typename Packet>
                                                                
                                   
                                                                     

                                                  
                                          
                                        
                                             

                                        
                
 

template <>
                                                       
                               
 

template <>
                                                       
                               
 

template <typename Packet>
                                                                                
                                                                     
                                                     
                                        

                                             
                                                  
                                                                              

                                                         
                                                             
                                                            
                
 

template <>
                                                                                   
                                 
 

template <>
                                                                                   
                                 
 
#endif

//---------- bfloat16 ----------
// TODO: Add support for native armv8.6-a bfloat16_t

// TODO: Guard if we have native bfloat16 support
typedef eigen_packet_wrapper<uint16x4_t, 19> Packet4bf;

template <>
struct is_arithmetic<Packet4bf> {
  enum { value = true };
};

template <>
struct packet_traits<bfloat16> : default_packet_traits {
  typedef Packet4bf type;
  typedef Packet4bf half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 4,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 1,
    HasAbs = 1,
    HasArg = 0,
    HasAbsDiff = 1,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,
    HasDiv = 1,
    HasSin = EIGEN_FAST_MATH,
    HasCos = EIGEN_FAST_MATH,
    HasLog = 1,
    HasExp = 1,
    HasSqrt = 0,
    HasTanh = EIGEN_FAST_MATH,
    HasErf = EIGEN_FAST_MATH,
    HasBessel = 0,  // Issues with accuracy.
    HasNdtri = 0
  };
};

template <>
struct unpacket_traits<Packet4bf> : neon_unpacket_default<Packet4bf, bfloat16> {};

namespace detail {
template <>
                                                                                
                                            
                  
                  
 
}  // namespace detail

                                                            
                                                                                 
                                    
                                                        

                            
                                                                    

                                 
                                                                

                           
                                          

                        
                                 

                                                        
                                                 
                                         
                                           

                                          
                          
 

                                                            
                                                                        
 

                                                                                                                  

template <>
                                                                      
                                                 
 

template <>
                                                                       
                                                                                                          
 

template <>
                                                                      
                   
                                                                                                                        
 

template <>
                                                                       
                                                                               
 

template <>
                                                                                
                                     
                                                                                                    
 

template <>
                                                                                 
                                                                              
 

template <>
                                                                         
                                                                                 
 

template <>
                                                        
                                                 
 

template <>
                                                                                                         
                                                                                 
 
template <>
                                                                                                     
                                                                             
 

template <>
                                                                                       
                                                               
 

template <>
                                                                                                         
                                                                                 
 
template <>
                                                                                                     
                                                                             
 

template <>
                                                                                       
                                                               
 

template <>
                                                                   
                                                           
 

template <>
                                                                           
                                                               
 

template <>
                                                                            
                                                                
 

template <>
                                                                            
                                                                
 

template <>
                                                                               
                                                                   
 

template <>
                                                                                                                        
                                                                                    
 

template <>
                                                                    
                                                  
 

template <>
                                                                     
                                                   
 

template <>
                                                                    
                                                  
 

template <>
                                                                     
                                                   
 

template <>
                                                                     
                                                   
 

template <>
                                                         
           
 

template <>
                                                                                       
                                                               
 

template <>
                                                                                       
                                                               
 

template <>
                                                                                       
                                                               
 

template <>
                                                                                                            
                                                                              
 

template <>
                                                                                                            
                                                                              
 

template <>
                                                                                                             
                                                                               
 

template <>
                                                                                                             
                                                                               
 

template <>
                                                                                       
                                                               
 

template <>
                                                                                                
                                                                                                  
 

template <>
                                                                                                           
                                                                                          
 

template <>
                                                                    
                                                               
 

template <>
                                                                        
                                                                   
 

template <>
                                                                        
                                                                   
 

template <>
                                                                        
                                                                   
 

template <>
                                                                       
                                                      
 

                                                                                          
                                  
 

template <>
                                                                                           
                                                                   
 

template <>
                                                                                          
                                                                          
 

template <>
                                                                                          
                                                                          
 

template <>
                                                                                                 
                                                                                 
 

template <>
                                                                                          
                                                                          
 

template <>
                                                                      
                                                                                                   
 

//---------- double ----------

// Clang 3.5 in the iOS toolchain has an ICE triggered by NEON intrinsics for double.
// Confirmed at least with __apple_build_version__ = 6000054.
#if EIGEN_COMP_CLANGAPPLE
// Let's hope that by the time __apple_build_version__ hits the 601* range, the bug will be fixed.
// https://gist.github.com/yamaya/2924292 suggests that the 3 first digits are only updated with
// major toolchain updates.
#define EIGEN_APPLE_DOUBLE_NEON_BUG (EIGEN_COMP_CLANGAPPLE < 6010000)
#else
#define EIGEN_APPLE_DOUBLE_NEON_BUG 0
#endif

#if EIGEN_ARCH_ARM64 && !EIGEN_APPLE_DOUBLE_NEON_BUG

#if EIGEN_COMP_GNUC
// Bug 907: workaround missing declarations of the following two functions in the ADK
// Defining these functions as templates ensures that if these intrinsics are
// already defined in arm_neon.h, then our workaround doesn't cause a conflict
// and has lower priority in overload resolution.
// This doesn't work with MSVC though, since the function names are macros.
template <typename T>
uint64x2_t vreinterpretq_u64_f64(T a) {
  return (uint64x2_t)a;
}

template <typename T>
float64x2_t vreinterpretq_f64_u64(T a) {
  return (float64x2_t)a;
}
#endif

#if EIGEN_COMP_MSVC_STRICT
typedef eigen_packet_wrapper<float64x2_t, 18> Packet2d;
typedef eigen_packet_wrapper<float64x1_t, 19> Packet1d;

                                                                
                          
                         
 

#else
typedef float64x2_t Packet2d;
typedef float64x1_t Packet1d;

                                                                                         
#endif

// functionally equivalent to _mm_shuffle_pd in SSE (i.e. shuffle(m, n, mask) equals _mm_shuffle_pd(m,n,mask))
// Currently used in LU/arch/InverseSize4.h to enable a shared implementation
// for fast inversion of matrices of size 4.
                                                                                      
                                                        
                                                        
                                                                            
             
 

                                                                                             
                             
 
                                                                                                              
                                                                                                              
#define vec2d_duplane(a, p) Packet2d(vdupq_laneq_f64(a, p))

template <>
struct packet_traits<double> : default_packet_traits {
  typedef Packet2d type;
  typedef Packet2d half;
  enum {
    Vectorizable = 1,
    AlignedOnScalar = 1,
    size = 2,

    HasCmp = 1,
    HasAdd = 1,
    HasSub = 1,
    HasShift = 1,
    HasMul = 1,
    HasNegate = 1,
    HasAbs = 1,
    HasArg = 0,
    HasAbsDiff = 1,
    HasMin = 1,
    HasMax = 1,
    HasConj = 1,
    HasSetLinear = 1,

    HasDiv = 1,

#if EIGEN_ARCH_ARM64 && !EIGEN_APPLE_DOUBLE_NEON_BUG
    HasExp = 1,
    HasLog = 1,
    HasLog1p = 1,
    HasExpm1 = 1,
    HasPow = 1,
    HasATan = 1,
    HasATanh = 1,
#endif
    HasSin = EIGEN_FAST_MATH,
    HasCos = EIGEN_FAST_MATH,
    HasTan = EIGEN_FAST_MATH,
    HasSqrt = 1,
    HasRsqrt = 1,
    HasCbrt = 1,
    HasTanh = EIGEN_FAST_MATH,
    HasErf = EIGEN_FAST_MATH,
    HasErfc = EIGEN_FAST_MATH
  };
};

template <>
struct unpacket_traits<Packet2d> : neon_unpacket_default<Packet2d, double> {
  using integer_packet = Packet2l;
};

template <>
                                                                     
                          
 

template <>
                                                                  
                           
 

template <>
                                                               
                                
                                                     
 

template <>
                                                                                   
                         
 

template <>
                                                                                   
                         
 

template <>
EIGEN_STRONG_INLINE Packet2d pxor<Packet2d>(const Packet2d&, const Packet2d&);
template <>
                                                                                      
                                                                                            
                                
 

template <>
                                                         
                      
 

template <>
                                                       
           
 

template <>
                                                                                   
                         
 

template <>
                                                                                   
                         
 

#ifdef EIGEN_VECTORIZE_FMA
// See bug 936. See above comment about FMA for float.
template <>
                                                                                             
                            
 
template <>
                                                                                              
                            
 
#else
template <>
                                                                                             
                            
 
template <>
                                                                                              
                            
 
#endif
template <>
                                                                                             
                                  
 
template <>
                                                                                              
                                 
 
template <>
                                                                                   
                         
 

#ifdef __ARM_FEATURE_NUMERIC_MAXMIN
// numeric max and min are only available if ARM_FEATURE_NUMERIC_MAXMIN is defined (which can only be the case for Armv8
// systems).
template <>
                                                                                                     
                           
 
template <>
                                                                                                     
                           
 

#endif

template <>
                                                                                                 
                              
 

template <>
                                                                                   
                         
 

template <>
                                                                                                 
                              
 

// Logical Operations are not supported for float, so we have to reinterpret casts using NEON intrinsics
template <>
                                                                                   
                                                                                              
 

template <>
                                                                                  
                                                                                              
 

template <>
                                                                                   
                                                                                              
 

template <>
                                                                                      
                                                                                              
 

template <>
                                                                            
                                                
 

template <>
                                                                            
                                                
 

template <>
                                                                                   
                                                                                  
 

template <>
                                                                            
                                                
 

template <>
                                                                  
                                                                                                        
 

template <>
                                                                   
                                                    
 

template <>
                                                                     
                             
 
template <>
                                                                           
                                                                                                      
 

template <>
                                                                            
                                                  
 

template <>
                                                                                                            
                                      
                                                  
                                                  
             
 

template <>
                                                                                                                       
                                           
                                           
 

template <>
                                                               
                           
 

// FIXME only store the 2 first elements ?
template <>
                                                                
                              
 

template <>
                                                          
                                                         
 

template <>
                                                      
                      
 

template <>
                                                          
                                                                          
 

template <>
                                                                
                       
 

// Other reduction functions:
// mul
#if                      
           
                                                                    
                                                 
 
     
           
                                                                    
                                                                       
 
      

      
           
                                                                    
                       
 

      
           
                                                                    
                       
 

                                                                                         
                                                                          
                                                                          

                          
                          
 

           
                                                                                                                    
                                                      
 

           
                                                                 
                       
 

           
                                                                  
                       
 

           
                                                                 
                       
 

           
                                                                  
                       
 

           
                                                                  
                      
 

           
                                                                                            
                                     
 

           
                                                                                      
                                     
 

           
                                                                     
                                                  
 

           
                                                        
                                        
                                                                                   
 

           
                                                        
                        
 

                                                           

                                                           
                                          
                              
                              

           
                                                           
                         
                         
        
                     
                        
             

               
                
               
               
                 
               
                  
               
               
                   
               
               
                
                     
                  
                  
               
               
               
               
               
                                                                             
                
                 
                             
                                            
                
    
 ;

template <>
struct unpacket_traits<Packet4hf> : neon_unpacket_default<Packet4hf, half> {};
template <>
struct unpacket_traits<Packet8hf> : neon_unpacket_default<Packet8hf, half> {
  using half = Packet4hf;
};

template <>
                                                                                            
                                                     
 

template <>
                                                                         
                             
 

template <>
                                                                         
                            
 

template <>
                                                                      
                                                 
                                     
                                                   
 

template <>
                                                                      
                                     
                                    
                                                  
 

template <>
                                                                                       
                         
 

template <>
                                                                                       
                        
 

template <>
                                                                                       
                         
 

template <>
                                                                                       
                        
 

template <>
                                                           
                      
 

template <>
                                                           
                     
 

template <>
                                                         
           
 

template <>
                                                         
           
 

template <>
                                                                                       
                         
 

template <>
                                                                                       
                        
 

template <>
                                                                                       
                         
 

template <>
                                                                                       
                        
 

template <>
                                                                                                 
                            
 

template <>
                                                                                                 
                           
 

template <>
                                                                                                  
                            
 

template <>
                                                                                                  
                           
 

template <>
                                                                                                 
                                  
 

template <>
                                                                                                 
                                  
 

template <>
                                                                                                  
                                 
 

template <>
                                                                                                  
                                 
 

template <>
                                                                                       
                         
 

template <>
                                                                                       
                        
 

#ifdef __ARM_FEATURE_NUMERIC_MAXMIN
// numeric max and min are only available if ARM_FEATURE_NUMERIC_MAXMIN is defined (which can only be the case for Armv8
// systems).
template <>
                                                                                                         
                          
 
template <>
                                                                                                         
                           
 
#endif

template <>
                                                                                                     
                               
 

template <>
                                                                                                     
                               
 

template <>
                                                                                       
                         
 

template <>
                                                                                       
                        
 

#ifdef __ARM_FEATURE_NUMERIC_MAXMIN
// numeric max and min are only available if ARM_FEATURE_NUMERIC_MAXMIN is defined (which can only be the case for Armv8
// systems).
template <>
                                                                                                         
                          
 
template <>
                                                                                                         
                           
 
#endif

template <>
                                                                                                     
                               
 

template <>
                                                                                                     
                               
 

#define EIGEN_MAKE_ARM_FP16_CMP_8(name)                                               \
  template <>                                                                         \
  EIGEN_STRONG_INLINE Packet8hf pcmp_##name(const Packet8hf& a, const Packet8hf& b) { \
    return vreinterpretq_f16_u16(vc##name##q_f16(a, b));                              \
  }

#define EIGEN_MAKE_ARM_FP16_CMP_4(name)                                               \
  template <>                                                                         \
  EIGEN_STRONG_INLINE Packet4hf pcmp_##name(const Packet4hf& a, const Packet4hf& b) { \
    return vreinterpret_f16_u16(vc##name##_f16(a, b));                                \
  }

                             
                             
                             

                             
                             
                             

#undef EIGEN_MAKE_ARM_FP16_CMP_8
#undef EIGEN_MAKE_ARM_FP16_CMP_4

template <>
                                                                                                 
                                                           
 

template <>
                                                                                                 
                                                        
 

template <>
                                                                    
                       
 

template <>
                                                                    
                      
 

template <>
                                                                     
                       
 

template <>
                                                                     
                      
 

template <>
                                                                    
                       
 

template <>
                                                                    
                      
 

template <>
                                                                     
                       
 

template <>
                                                                     
                      
 

template <>
                                                                     
                      
 

template <>
                                                                     
                     
 

template <>
                                                                    
                       
 

template <>
                                                                    
                      
 

template <>
                                                                                       
                                                                                              
 

template <>
                                                                                       
                                                                                          
 

template <>
                                                                                      
                                                                                              
 

template <>
                                                                                      
                                                                                          
 

template <>
                                                                                       
                                                                                              
 

template <>
                                                                                       
                                                                                          
 

template <>
                                                                                          
                                                                                              
 

template <>
                                                                                          
                                                                                          
 

template <>
                                                                         
                                            
                                                                                                       
 

template <>
                                                                         
                                           
                                                                                                       
 

template <>
                                                                          
                                                                                        
 

template <>
                                                                          
                                                                                       
 

template <>
                                                                            
                   
                        
                        
                        
                        
                        
                        
                        
                        
                
 

template <>
                                                                            
                     
                 
                            
                     
                     
                     
                     
                
 

template <>
                                                                             
                   
                                                              
                                                                  
                              
 

                                                                                                 
                                   
 

                                                                                                 
                                  
 

template <>
                                                                                                                        
                                                      
 

template <>
                                                                                                                        
                                                    
 

                                                                                                
                                   
 

                                                                                                
                                  
 

template <>
                                                                                      
                                      
                                                                                                     
 

template <>
                                                                                      
                                     
                                                                                                     
 

template <>
                                                                                       
                                                                                
 

template <>
                                                                                       
                                                                               
 

template <>
                                                                                                                        
                                                     
                                                   
                                                   
                                                   
                                                   
                                                   
                                                   
                                                   
                                                   
             
 

template <>
                                                                                                                        
                                                     
                                                  
                                                  
                                                  
                                                  
             
 

template <>
                                                                                                                   
                                                                                           
                                             
                                             
                                             
                                             
                                             
                                             
                                             
                                             
 

template <>
                                                                                                                   
                                                                                           
                                            
                                            
                                            
                                            
 

template <>
                                                                         
                           
 

template <>
                                                                       
                 
                  
                
             
           
 

template <>
                                                                       
                 
                 
                
             
           
 

template <>
                                                            
                         
                  

                         
                             
                              
                                  
 

template <>
                                                                       
                       
 

template <>
                                                                   
                      
 

template <>
                                                            
                                                                          
 

template <>
                                                                   
                     
 

template <>
                                                            
                                                                       
 

template <>
                                                                       
                              

                         
                          
                              
                            
                            

                
                              
           
 

template <>
                                                                       
                  

                        
                            
                
                              
           
 

template <>
                                                                           
                               

                         
                          
                              
                                          

                
                                                                  
           
 

template <>
                                                                           
                   
                                    
                
                                                                  
           
 

template <>
                                                                           
                
                      
           
 

template <>
                                                                           
                
                     
           
 

template <>
                                                                           
                
                      
           
 

template <>
                                                                           
                
                     
           
 

                                                                                          
                                                                              
                                                                              

                                                                                                                        
                                                                                                                        

                                                           
                                                           
                                                           
                                                           
 

                                                                                          
                                     
                                       
                         

                                   
                                   
                                   
                                   
 

                                                                                          
                       

                                                         
                                                         
                                                         
                                                         

                       
                                                   
                                                   
                                                   
                                                   

                       
                                                   
                                                   
                                                   
                                                   

                                   
                                   
                                   
                                   
                                   
                                   
                                   
                                   
 
#endif  // end EIGEN_HAS_ARM64_FP16_VECTOR_ARITHMETIC

}  // end namespace internal

}  // end namespace Eigen

#endif  // EIGEN_PACKET_MATH_NEON_H