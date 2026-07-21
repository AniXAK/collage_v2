<script setup>

</script>

<template>
<div class="fon">
    <div class="square"></div>
    <div class="square"></div>
    <div class="square" style="margin-right: 0px;"></div>
</div>
</template>

<style>
*{
  box-sizing: border-box;
}
html, body {
  padding: 0;
  margin: 0;
  font-family: verdana, arial, sans-serif;  
}
.fon{
    background-color: rgb(255, 255, 255);
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: center;
    height: 180px;
    width: 500px;
}
.square{
    background-color: rgb(227, 233, 239);
    width: 140px;
    height: 140px;
    margin-right: 20px;
}
</style>