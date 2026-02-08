import { Dashboard } from './dashboard';
import { iUser } from '../App';
import { Button, Divider, Typography } from '@mui/material';
import { Person as UserIcon } from '@mui/icons-material';

export const Header = (user:iUser) => {

    return <>
          <div style={{textAlign: 'right'}}>
            <Button variant="outlied" endIcon={<UserIcon />} >
                {user && user.username && user.username}
            </Button>
            
          </div>
          <Divider />
    </>
}
