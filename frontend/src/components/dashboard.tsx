import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../common/constants';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import { CardContent, Typography } from '@mui/material';

import { To, useNavigate } from 'react-router-dom';


interface iPanel {
  value: string,
  text: string,
  link: To,
}


interface iData {
  mitgliedercount?: {
    aktiv: number,
    inaktiv: number
  } | undefined,
  institutionencount?: {
    aktiv: number,
    inaktiv: number
  },
  abonnentcount?: {
    aktiv: number,
    inaktiv: number
  },
  jubilare?: number[],
  mitgliedsarten?: string,
  berufecount?: string,
  laendercount?: string
}


const DashPanel = ({value, text, link}: iPanel) => {
      const navigate = useNavigate();

      function handleClick() {
        navigate(link, {replace: true})
      }


      return <Grid>
          <Card onClick={handleClick} elevation={3} variant="outlined">
            <CardContent>
              <Typography gutterBottom sx={{ color: 'text.secondary', fontSize: 14 }}>
                {value}
              </Typography>
              <Typography variant="h5" component="div">
                {text}
              </Typography>
            </CardContent>
          </Card>
      </Grid>
}

export const Dashboard = () => {
  const [data, setData] = useState<iData>({});
  const [loading, setLoading] = useState(true);


  useEffect(() => {
    axios.get(API_URL + 'dashboard/').then(res => {
      setData(res.data)
    })
    setLoading(false)
  }, [])


    return <div>
      { loading ? <h2>Loading now</h2> :
        <Grid container spacing={3}>

          <Grid size={4}>
            <DashPanel value={data.mitgliedercount?.aktiv + " ("+data.mitgliedercount?.inaktiv+")"} text="Mitglieder" link='/members/'/>
          </Grid>
          <Grid size={4}>
            <DashPanel value={data.institutionencount?.aktiv + " ("+data.institutionencount?.inaktiv+")"} text="Institutionen" link='/institutionen/' />
          </Grid>
          <Grid size={4}>
            <DashPanel value={String(data.jubilare?.length)} text="Jubilare" link='/jubilare/' />
          </Grid>

          <Grid size={4}>
            <DashPanel value={data.abonnentcount?.aktiv + " (" + data.abonnentcount?.inaktiv + ")"} text="Abonnenten" link='/abonnenten/' />
          </Grid>
          
          <Grid size={4}>
            <DashPanel value={"Etiketten"} text="fürs VGI" link='/etiketten/' />
          </Grid>
        
          <Grid size={4}>
            <DashPanel value={"Finanz"} text="Übersicht" link='/finanzen/' />
          </Grid>
          <Grid size={4}>
            <DashPanel value={String(data.mitgliedsarten)} text="Mitgliedsarten" link='/mitgliedsarten/' />
          </Grid> 
          <Grid size={4}>
            <DashPanel value={String(data.berufecount)} text="Berufe" link='/berufe/' />
          </Grid>

          <Grid size={4}>
            <DashPanel value={String(data.laendercount)} text="Laender" link='/laender/' />
          </Grid>

        </Grid>
      }
      </div>
}

export default Dashboard;