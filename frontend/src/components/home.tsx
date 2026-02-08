import { Dashboard } from './dashboard';
import { iUser } from '../App';


export const Home = (user:iUser) => {

    return <>
        <h1>das ist die Home-Seite von {user.username}</h1>
        <Dashboard />
    </>
}
