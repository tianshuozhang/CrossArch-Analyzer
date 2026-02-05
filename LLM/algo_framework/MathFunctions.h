// This file is part of Eigen, a lightweight C++ template library
// for linear algebra.
//
// This Source Code Form is subject to the terms of the Mozilla
// Public License v. 2.0. If a copy of the MPL was not distributed
// with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

#ifndef EIGEN_MATH_FUNCTIONS_NEON_H
#define EIGEN_MATH_FUNCTIONS_NEON_H

// IWYU pragma: private
#include "../../InternalHeaderCheck.h"

namespace Eigen {

namespace internal {

                                                    
                                                    

#if EIGEN_HAS_ARM64_FP16_VECTOR_ARITHMETIC
template <>
                                                                                      
                                                                   
                                                        
 

template <>
                                                                                      
                                                                                     
                                                                                   
                                                                           
 
#endif  // EIGEN_HAS_ARM64_FP16_VECTOR_ARITHMETIC

                           
                                               
                                               
                                               
                                                
                                                

template <>
                                                                               
                     
                                                                             
                                  
             
 

template <>
                                                                                     
                                                                        
 

//---------- double ----------

#if EIGEN_ARCH_ARM64 && !EIGEN_APPLE_DOUBLE_NEON_BUG

                                                     

#endif

}  // end namespace internal

}  // end namespace Eigen

#endif  // EIGEN_MATH_FUNCTIONS_NEON_H