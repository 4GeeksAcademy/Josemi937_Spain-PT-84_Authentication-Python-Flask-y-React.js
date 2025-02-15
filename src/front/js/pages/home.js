import React, { useContext, useEffect } from "react";
import { Context } from "../store/appContext";
import rigoImageUrl from "../../img/rigo-baby.jpg";
import "../../styles/home.css";

export const Home = () => {
	const { store, actions } = useContext(Context);
	useEffect(()=>{
		actions.login()
	}, []) 

	return (
		<div className="text-center mt-5">
			<h1>Hello Rigo!!</h1>
			<p>
				<img src={rigoImageUrl} />
			</p>
			<div className="alert alert-info">
				{store.message || "Loading message from the backend (make sure your python backend is running)..."}
			</div>
			<button className="btn btn-success" onClick={()=>{
				actions.private()
			}}>Get Private</button>
			<button 
				className="btn btn-danger mt-3"
				onClick={() => actions.logout()}>
				Logout
			</button>
		</div>
	);
};
