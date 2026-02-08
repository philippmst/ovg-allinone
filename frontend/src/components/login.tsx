import { useState, useEffect } from "react";
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import axios from 'axios';

import { API_URL } from "../common/constants";

interface loginProps {
    loginUser: (user: iUser) => void
}

interface iUser {
    username?: string | undefined,
    password?: string | undefined
}

export const Login = ({loginUser}: loginProps) => {
    const [user, setUser] = useState<iUser>({});
    const [error, setError] = useState(false);
    const [formValid, setFormValid] = useState(false);

    useEffect(() => {
        if (error) {
            setTimeout(() => { setError(false) }, 1500)
        }
    }, [error])


    const handleChange = (e: { target: { id: string | number; value: string; }; }) => {
        const u = {...user}
        if (e.target.id === 'password') {
            u.password = e.target.value
        } else if (e.target.id === 'username') {
            u.username = e.target.value
        }
        setUser(u)
        if (u.username && u.password) {
            setFormValid(true)
        }
    }

    const login = () => {
        axios.post(API_URL + 'auth/login/', user).then(res => {
            loginUser(res.data.user)
            setError(false);
        }).catch(err => {
            console.log(err)
            setError(true);
        })
    }


    return <Container maxWidth="sm">
      <Paper elevation={12} style={{ marginTop: 150, marginLeft: 20, marginRight: 20, paddingBottom: 20, border: '1px solid lightgrey'}} className={error ? 'shaking' : ''}>
          <div className="App-header">
            <h2> Login</h2>
          </div>
          <Box component="form" 
                sx={{'& > :not(style)': { m: 1},}}
                style={{marginTop: 40, marginLeft: 10, marginRight: 30}}
                >
            <TextField
                required fullWidth
                id="username"
                label="Username"
                onChange={handleChange}
                />
            <TextField
                required fullWidth
                id="password"
                type="password"
                label="Password"
                onChange={handleChange}
                onKeyDown={ e => (e.keyCode === 13 ? login() : null )}
                />
            <Button
                onClick={login} 
                disabled={!formValid}
                variant="contained" component="label" style={{left: 200, textAlign: 'right'}}>Login</Button>
        </Box>
      </Paper>
      { error && <h2 style={{marginLeft: 40, color: 'red'}}>Anmeldung nicht erfolgreich!</h2>}

    </Container>

}