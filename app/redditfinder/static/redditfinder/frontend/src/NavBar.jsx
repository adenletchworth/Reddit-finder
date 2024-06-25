// NavBar.js
import React from 'react';
import { Icon } from '@iconify/react';
import homeIcon from '@iconify-icons/fa/home';
import infoCircle from '@iconify-icons/fa/info-circle';
import search from '@iconify-icons/fa/search';

const NavBar = ({ setCurrentPage }) => {
    return (
        <div className="bg-primary-dark fixed top-0 left-0 w-full h-20 m-0 flex flex-row items-center justify-around shadow-lg">
            <NavBarIcon icon={homeIcon} onClick={() => setCurrentPage('home')} />
            <NavBarIcon icon={search} onClick={() => setCurrentPage('search')} />
            <NavBarIcon icon={infoCircle} onClick={() => setCurrentPage('info')} />
        </div>
    );
};

const NavBarIcon = ({ icon, onClick }) => (
    <div className="navbar-icon" onClick={onClick}>
        <Icon icon={icon} width="28" height="28"/>
    </div>
);

export default NavBar;
