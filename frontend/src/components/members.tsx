import { Container } from '@mui/material';
import { iUser } from '../App';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../common/constants';


export const Members = (user:iUser) => {
    const [loading, setLoading] = useState(true)
    const [members, setMembers] = useState(false)

    useEffect(() => {
        axios.get(API_URL + 'vereinsmitglieder/').then(res => {
            setMembers(res.data)
        })
        setLoading(false)
    }, [])

    return <>
        <Container>
            <h1>das ist die Members-Seite von {user.username}</h1>
            {!loading && members && members.results.map((member,i) => (
                    
                    <li key={i}>{member.first_name} {member.last_name}</li>
                ))
            }
            
            
        </Container>
    </>
}
