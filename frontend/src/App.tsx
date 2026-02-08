import { useState, useEffect } from 'react'
import './App.css'
import axios from 'axios';
import { API_URL } from "./common/constants";

import { Login } from './components/login';
import { Home } from './components/home';
import { Members } from './components/members';
import { Header } from './components/header';
import { Routes, Route } from 'react-router-dom';

export interface iUser {
  username?: string
}




const App = () => {
  const [user, setUser] = useState<iUser>();
  console.log(user)

  useEffect(() => {
    axios.get(API_URL + 'verifyToken')
      .then(res => setUser(res.data.user))
      .catch(() => setUser({username: 'bipo'}))
      .catch(() => setUser({}))
  }, [])

  
  return (
    <>
      {!user?.username ? <Login loginUser={setUser} /> : <>
          <Header {...user} />
          <Routes>
            <Route path="/" element={<Home {...user} />} />
            <Route path="/members" element={<Members {...user} />} />
          </Routes>

        </>}
    </>
  )
}

export default App