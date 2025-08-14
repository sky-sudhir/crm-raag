import useMutation from '@/hooks/useMutation'
import { AUTH_VERIFY } from '@/imports/api'
import React, { useEffect } from 'react'
import {  useNavigate, useSearchParams } from 'react-router-dom'
import { setToken, setUser } from "@/redux/features/user/userSlice";
import { useDispatch } from 'react-redux'


function VerifyPage() {
    const [param]=useSearchParams()
  const dispatch = useDispatch();

    const navigate=useNavigate()
    const token=param.get("token")
    
    const {mutate}=useMutation()
    const verifyEmail=async()=>{

        const response=await mutate({url:`${AUTH_VERIFY}?token=${token}`,method:"GET"})
        if(response.success){
            dispatch(setUser({ ...response?.data?.data,token:null }));
            dispatch(setToken({ token: response?.data?.data?.token }));
            navigate('/home')
        }else{
         navigate("/auth")

        }
console.log(response,'qqqqqqqq')
    }

    useEffect(() => {
     if(token){
        verifyEmail()
    }else{
         navigate("/auth")

     }
    }, [])
    


  return (
    <div>VerifyPage</div>
  )
}

export default VerifyPage